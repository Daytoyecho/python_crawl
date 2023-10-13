# -*- coding:utf-8 -*-
from copy import deepcopy
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl province_laws_61


class ProvinceLaw61Spider(scrapy.Spider):
    name = 'province_laws_61'
    allowed_domains = ['shandong.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.shandong.gov.cn/module/search/index.jsp?field=field_1244:1:1&i_columnid=107861&field_1244=&currpage={}"
        start_url = ['http://www.shandong.gov.cn/module/search/index.jsp?field=field_1244:1:1&i_columnid=107861&field_1244=&currpage=1']

        for i in range(2, 1016):
            start_url.append(base.format(str(i)))

        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.shandong.gov.cn/col/col107861/index.html'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            time.sleep(3)
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//div[@class="zcjd-list"]/ul/li')

        for item in data_list:
            tmpurl = item.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, "http://www.shandong.gov.cn/col/col107861/index.html")
            law_title = item.xpath('./a/@title').extract_first()
            law_time = tools.clean(item.xpath('./span/text()').extract_first())[:10]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "山东省政府-省政府及省政府办公厅文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="wip_art_con"]').extract_first()
            fujian = response.xpath('//div[@class="wip_art_con"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="wip_art_con"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//div[@class="people-desc"]//tr/td/strong[contains(text(),"发文字号")]/../text()').extract_first()
            if wenhao and re.search(r'号', wenhao) and len(tools.clean(wenhao)) < 25:
                item["legalDocumentNumber"] = tools.clean(wenhao)

            item['legalContent'] = content
            tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.url)
        else:
            tools.xaizai_not_html_zw(pdf_name, response.body)
        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.url)
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
