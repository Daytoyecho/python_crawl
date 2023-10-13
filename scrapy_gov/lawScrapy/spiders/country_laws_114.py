# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_114


class CountryLaw114Spider(scrapy.Spider):
    name = 'country_laws_114'
    allowed_domains = ['chinaclear.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = ['http://www.chinaclear.cn/zdjs/fbzyls/service_tlist.shtml']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="pageTabContent"]/ul//li/a/@href').extract()
        law_title = response.xpath('//div[@class="pageTabContent"]/ul//li/a/text()').extract()
        law_time = response.xpath('//div[@class="pageTabContent"]/ul//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中国证券登记结算有限责任公司"
        item["legalCategory"] = "中国结算-服务支持-收费标准"
        if response.url in self.url_list:
            0/0
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        with open(pdf_name, 'wb')as f:
            f.write(response.body)

        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        item['legalScrapyTime'] = tools.getnowtime()
        return item
