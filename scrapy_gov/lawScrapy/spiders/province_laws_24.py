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

# scrapy crawl province_laws_24


class ProvinceLaw24Spider(scrapy.Spider):
    name = 'province_laws_24'
    allowed_domains = ['cq.gov.cn']
    count = 0
    url_list = []

    def start_requests(self):

        base = 'http://czj.cq.gov.cn/zwgk_268/fdzdgknr/lzyj/xzgfxwj/index_{}.html'
        start_url = ['http://czj.cq.gov.cn/zwgk_268/fdzdgknr/lzyj/xzgfxwj/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 7):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//ul[@class="xhy-c2rul-6"]//li/a/@href').extract()
        law_title = response.xpath('//ul[@class="xhy-c2rul-6"]//li/a/@title').extract()
        law_time = response.xpath('//ul[@class="xhy-c2rul-6"]//li/span[2]/text()').extract()

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

        item["legalProvince"] = "重庆市"
        item["legalCategory"] = "重庆市财政局-规范性文件"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="zwxl-article"]').extract_first()
            fujian = response.xpath('//div[@class="zwxl-article"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="zwxl-article"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//span[@class="con"][contains(text(),"号")]/text()').extract_first()
            if tmpn:
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
