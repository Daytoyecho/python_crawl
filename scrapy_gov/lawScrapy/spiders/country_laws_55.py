# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_55


class CountryLaw55Spider(scrapy.Spider):
    name = 'country_laws_55'
    allowed_domains = ['mof.gov.cn']
    url_list = []
    count = 0
    wrong = 0

    def start_requests(self):
        BASEURL = 'http://www.mof.gov.cn/gkml/bulinggonggao/tongzhitonggao/index_{}.htm'
        start_url = ['http://www.mof.gov.cn/gkml/bulinggonggao/tongzhitonggao/']

        for i in range(1, 23):
            start_url.append(BASEURL.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in start_url:
            yield scrapy.Request(i, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//ul[@class="xwbd_lianbolistfrcon"]//li')
        for item in data_list:
            tmpurl = item.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)

            law_title = item.xpath('./a/@title').extract_first()
            law_time = item.xpath('./span/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, 'time': law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        if re.search(r'/404\.htm', response.url):
            self.wrong += 1
            print(self.wrong)
            0/0
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国财政部"
        item["legalCategory"] = "财政部通知公告更新"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            try:
                tmpn = tools.clean(response.xpath('//div[@class="TRS_Editor"]/p[1]').xpath('string(.)').extract_first())
                if re.search(r'[0-9]', tmpn) and len(tmpn) < 20 and '日' not in tmpn:
                    item["legalDocumentNumber"] = tmpn
            except:
                pass
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            if not content:
                content = response.xpath('//div[@class="my_conboxzw"]').extract_first()
            fujian = response.xpath('//ul[@id="down1"]/li/span/a/@href').extract()
            fujian_name = response.xpath('//ul[@id="down1"]/li/span/a').xpath('string(.)').extract()

            content = re.sub(r'<div class="conbottom[\s\S]+?<div class="conboxdown[\s\S]+?</div>', r"", content)
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
