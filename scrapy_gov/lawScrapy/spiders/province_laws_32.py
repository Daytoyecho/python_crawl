# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl province_laws_32


class ProvinceLaw32Spider(scrapy.Spider):
    name = 'province_laws_32'
    allowed_domains = ['gz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = ["http://jrjgj.gz.gov.cn/zwgk/xxgk/zcjd/index.html",
                     "http://jrjgj.gz.gov.cn/zwgk/xxgk/zcjd/index_2.html",
                     "http://jrjgj.gz.gov.cn/zwgk/xxgk/zcjd/index_3.html",
                     "http://jrjgj.gz.gov.cn/zwgk/xxgk/zcjd/index_4.html"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        law_url_list = response.xpath('//div[@class="mainContent"]//li/a/@href').extract()
        law_title = response.xpath('//div[@class="mainContent"]//li/a/@title').extract()
        law_time = response.xpath('//div[@class="mainContent"]//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "广东省"
        item["legalCategory"] = "广州市地方金融监督管理局-政策解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="info_cont"]').extract_first()
            fujian = response.xpath('//div[@class="info_cont"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="info_cont"]//a[@href]').xpath('string(.)').extract()

            for i in response.xpath('//div[@class="info_cont"]//p').xpath('string(.)').extract():
                if not i:
                    continue
                if len(tools.clean(i)) < 20:
                    tmpn = re.search(r"([\S]{0,15}[\[〔][0-9]{4}[〕\]][0-9]+号)", tools.clean(i))
                    if tmpn:
                        item["legalDocumentNumber"] = tmpn.group(1)

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
