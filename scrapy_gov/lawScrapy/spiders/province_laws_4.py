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

# scrapy crawl province_laws_4


class ProvinceLaw4Spider(scrapy.Spider):
    name = 'province_laws_4'
    allowed_domains = ['beijing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://www.beijing.gov.cn/zhengce/dfxfg/index_{}.html'
        start_url = ['http://www.beijing.gov.cn/zhengce/dfxfg/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 9):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//div[@class="listBox"]//li')

        for item in data_list:
            tmpurl = item.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
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
        item["legalCategory"] = "北京市政府-地方性法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            item["legalPublishedTime"] = response.xpath('//ol[contains(@class,"doc-info")]/li[contains(text(),"发布日期")]/span/text()').extract_first()
            fujian = response.xpath('//ul[@class="fujian"]//a/@href').extract()
            fujian_name = response.xpath('//ul[@class="fujian"]//a[@href]').xpath('string(.)').extract()
            try:
                tmpn = response.xpath('//li[@class="fwzh"]/span/text()').extract_first()
                if re.search('[0-9]+', tmpn):
                    item["legalDocumentNumber"] = tools.clean(tmpn)
            except:
                pass
            content = response.xpath('//div[@id="mainText"]').extract_first()
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
