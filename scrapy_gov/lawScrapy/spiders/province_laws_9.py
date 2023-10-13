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

# scrapy crawl province_laws_9


class ProvinceLaw9Spider(scrapy.Spider):
    name = 'province_laws_9'
    allowed_domains = ['beijing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = ['http://jrj.beijing.gov.cn/zcfg/bjszcfg/',
                     'http://jrj.beijing.gov.cn/zcfg/bjszcfg/index_1.html',
                     "http://jrj.beijing.gov.cn/zcfg/bjszcfg/index_2.html"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//div[@class="dancon-list"]//li')

        for item in data_list:
            url = item.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(url, response.url)

            law_title = item.xpath('./a/@title').extract_first()
            law_time = item.xpath('./span/text()').extract_first().strip()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "北京市"
        item["legalCategory"] = "北京市地方金融监督管理局-政策法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = response.meta['time'].strip()

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@class="zhengwen"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="zhengwen"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@class="zhengwen"]').extract_first()
            if not content:
                print("************************************", response.url, "************************************")
            if re.search("京[\s\S]{0,5}〔[0-9]{4}〕[0-9]+?号", content):
                item["legalDocumentNumber"] = re.search("(京[\s\S]{0,5}〔[0-9]{4}〕[0-9]+?号)", content).group(1)
            elif re.search("〔", content):
                item["legalDocumentNumber"] = "人工审查"

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
