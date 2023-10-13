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

# scrapy crawl province_laws_14_21


class ProvinceLaw14_21Spider(scrapy.Spider):
    name = 'province_laws_14_21'
    allowed_domains = ['tj.gov.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.tj.gov.cn/zwgk/szfwj/index_{}.html'
        start_url = ['http://www.tj.gov.cn/zwgk/szfwj/index.html']
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 67):
            start_url.append(base.format(str(i)))
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="list-circle-red"]//a/@href').extract()
        law_title = response.xpath('//div[@class="list-circle-red"]//a/@title').extract()
        law_time = response.xpath('//div[@class="list-circle-red"]/div/span/text()').extract()

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

        item["legalProvince"] = "天津市"
        item["legalCategory"] = "天津市政府-津政办规、津政发、津政令、津政函、津政办发、津政办函、津政规"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="article_content xl-zw-info"]').extract_first()
            fujian = response.xpath('//div[@class="article_content xl-zw-info"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="article_content xl-zw-info"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//div[@class="top-container"]//div[contains(text(),"津政")]/text()').extract_first()
            if tmpn:
                item["legalDocumentNumber"] = tmpn
            else:
                for i in response.xpath('//div[@class="article_content xl-zw-info"]//p').xpath('string(.)').extract():
                    if re.search("第[0-9]号", i) and len(tools.clean(i) < 10):
                        item["legalDocumentNumber"] = tools.clean(response.xpath('//div[@class="article_content xl-zw-info"]//p[1]').xpath('string(.)').extract_first() + i)

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
