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

# scrapy crawl province_laws_2


class ProvinceLaw2Spider(scrapy.Spider):
    name = 'province_laws_2'
    allowed_domains = ['beijing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base1 = 'http://www.beijing.gov.cn/zhengce/zfwj/zfwj/bgtwj/index_{}.html'
        base2 = 'http://www.beijing.gov.cn/zhengce/zfwj/zfwj2016/bgtwj/index_{}.html'
        start_url = ['http://www.beijing.gov.cn/zhengce/zfwj/zfwj/bgtwj/', 'http://www.beijing.gov.cn/zhengce/zfwj/zfwj2016/bgtwj/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 109):
            start_url.append(base1.format(str(i)))
        for i in range(1, 15):
            start_url.append(base2.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        if not re.search(r"/zfwj/zfwj2016/", response.url):
            data_list = response.xpath('//div[@class="listBox"]//li')

            for item in data_list:
                tmpurl = item.xpath('./a/@href').extract_first()
                tmpurl = tools.getpath(tmpurl, response.url)
                law_title = item.xpath('./a/@title').extract_first()
                try:
                    law_document_number = item.xpath('./span/text()').extract_first().strip()
                except:
                    law_document_number = ""
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "DocumentNumber": law_document_number}, dont_filter=False, headers=tools.header)
        else:
            data_list = response.xpath('//div[@class="left"]//li')
            for item in data_list:
                tmpurl = item.xpath('./a/@href').extract_first()
                tmpurl = tools.getpath(tmpurl, response.url)
                law_title = item.xpath('./a/@title').extract_first()
                try:
                    law_document_number = item.xpath('./span/text()').extract_first().strip()
                except:
                    law_document_number = ""
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "DocumentNumber": law_document_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "北京市"
        item["legalCategory"] = "北京市政府-市政府办公厅文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        if response.meta['DocumentNumber']:
            item["legalDocumentNumber"] = response.meta['DocumentNumber']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            item["legalPublishedTime"] = response.xpath('//ol[contains(@class,"doc-info")]/li[contains(text(),"发布日期")]/span/text()').extract_first()
            fujian = response.xpath('//ul[@class="fujian"]//a/@href').extract()
            fujian_name = response.xpath('//ul[@class="fujian"]//a[@href]').xpath('string(.)').extract()

            content = response.xpath('//div[@id="mainText"]').extract_first()
            content = '<div style="overflow: hidden;margin: 0 auto;width: 100%;">' + content + '</div>'
            content = re.sub('bgcolor="#000000', "", content)
            content = re.sub('<div id="mainText">', '<div id="mainText" style="margin: 0 auto;width: 100%;color: #404040;font-size: 16px;line-height: 200%;padding: 0 0 25px 0;">', content)
            content = re.sub('<div id="wenjian"> ', '<div id="wenjian" style="margin: 0 auto;text-align: center;display: block;">', content)
            content = re.sub('<table', "<table align='center'", content)

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
