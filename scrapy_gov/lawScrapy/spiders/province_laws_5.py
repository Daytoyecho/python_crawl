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

# scrapy crawl province_laws_5


class ProvinceLaw5Spider(scrapy.Spider):
    name = 'province_laws_5'
    allowed_domains = ['beijing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://www.beijing.gov.cn/gongkai/zfxxgk/zc/gz/index_{}.html'
        start_url = ['http://www.beijing.gov.cn/gongkai/zfxxgk/zc/gz/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 14):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//div[@class="m-list"]/ul/li[2]')

        for item in data_list:
            tmpurl = item.xpath('./p[1]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./p[1]/a/text()').extract_first()
            law_time = re.search(r'[（\(]([0-9]+年[0-9]+月[0-9]+日)', item.xpath('./p[2]/text()').extract_first().strip()).group(1)
            try:
                law_number = re.search(r'月[0-9]+日([\s\S]+?第[0-9]+号)', item.xpath('./p[2]/text()').extract_first().strip()).group(1)
            except:
                law_number = ""
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, 'number': law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "北京市"
        item["legalCategory"] = "北京市政府-政府规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'], "%Y年%m月%d日"))
        if response.meta['number']:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@class="m-container"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="m-container"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@class="mainTextBox"]').extract_first()

            if re.search("〔", content):
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
