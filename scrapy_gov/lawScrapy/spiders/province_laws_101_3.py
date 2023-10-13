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

# scrapy crawl province_laws_101_3


class ProvinceLaw101Spider(scrapy.Spider):
    name = 'province_laws_101_3'
    allowed_domains = ['xinjiang.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        # 只有一页
        start_url = ['http://jrjgj.xinjiang.gov.cn/jrb/dfjr/list.shtml']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://jrjgj.xinjiang.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="list_r"]//li/a/@href').extract()
        law_title = response.xpath('//div[@class="list_r"]//li/a/text()').extract()
        law_time = response.xpath('//div[@class="list_r"]//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "新疆维吾尔自治区"
        item["legalCategory"] = "新疆维吾尔自治区地方金融监督管理局-政策法规"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if re.search(r'(新.*?[0-9]{0,4}.*?号)', response.meta['title']):
            item["legalDocumentNumber"] = re.search(r'(新.*?[0-9]{0,4}.*?号)', response.meta['title']).group(1)
        else:
            item["legalDocumentNumber"] = ""

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="content"]').extract_first()
            fujian = response.xpath('//*[@id="content"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="content"]//a[@href]').xpath('string(.)').extract()

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
