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

# scrapy crawl province_laws_104


class ProvinceLaw104Spider(scrapy.Spider):
    name = 'province_laws_104'
    allowed_domains = ['shaanxi.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/xzgfxwj/index_{}.html'
        start_url = ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/xzgfxwj/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://www.shaanxi.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 6):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//ul[@class="gov-item cf-otw"]//li//a/@href').extract()
        law_title = response.xpath('//ul[@class="gov-item cf-otw"]//li//a/@title').extract()
        law_time = response.xpath('//span[@class="date rt"]/text()').extract()
        document_number = response.xpath('//span[@class="code-num otw lf"]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i], "number": document_number[i]}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "陕西省"
        item["legalCategory"] = "陕西省政府-行政规范性文件"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="doc_left"]').extract_first()
            fujian = response.xpath('//*[@id="doc_left"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="doc_left"]//a[@href]').xpath('string(.)').extract()

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
