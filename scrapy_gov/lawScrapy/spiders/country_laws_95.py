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

# scrapy crawl country_laws_95


class CountryLaw95Spider(scrapy.Spider):
    name = 'country_laws_95'
    allowed_domains = ['safe.gov.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.safe.gov.cn/safe/zcfg/index_{}.html'
        start_url = ['http://www.safe.gov.cn/safe/zcfg/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 27):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="list_conr"]//ul//li/dt/a/@href').extract()
        law_title = response.xpath('//div[@class="list_conr"]//ul//li/dt/a/@title').extract()
        law_time = response.xpath('//div[@class="list_conr"]//ul//li/dd/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国家外汇管理局"
        item["legalCategory"] = "国家外汇管理局-政策法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="content"]').extract_first()
            fujian = response.xpath('//div[@id="content"]//p//a/@href').extract()
            fujian_name = response.xpath('//div[@id="content"]//p//a[@href]').xpath('string(.)').extract()

            test = str(response.xpath('//*[@id="wh"]/text()').extract_first())
            if re.search(r'(.*[0-9]{0,4}.*号)', test):
                item["legalDocumentNumber"] = test

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
