# -*- coding:utf-8 -*-
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
import pdfkit
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

# scrapy crawl province_laws_99


class ProvinceLaw99Spider(scrapy.Spider):
    name = 'province_laws_99'
    allowed_domains = ['xinjiang.gov.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.xinjiang.gov.cn/xinjiang/gzk/search_gkgz_{}.shtml'
        start_url = ['http://www.xinjiang.gov.cn/xinjiang/gzk/search_gkgz.shtml']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 14):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//div[@class="gkgz_list_content"]/ul/li')

        for item in data_list:
            tmpurl = item.xpath('./div[@class="bt"]/p/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./div[@class="bt"]/p/a/@title').extract_first()
            law_text = item.xpath('./div[@class="bt"]/div/p/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "text": law_text}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "新疆维吾尔自治区"
        item["legalCategory"] = "新疆维吾尔自治区政府-政府规章"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        t = re.search(r'[（\(](.+?日)', response.meta['text']).group(1)
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(t, "%Y年%m月%d日"))

        wenhao = re.search(r'日(.+?号)', response.meta['text']).group(1)
        item["legalDocumentNumber"] = tools.clean(wenhao)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):

            content = response.xpath('//div[@class="gknbxq_detail"]').extract_first()
            fujian = response.xpath('//div[@class="gknbxq_detail"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="gknbxq_detail"]//a[@href]').xpath('string(.)').extract()

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
