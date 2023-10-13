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

# scrapy crawl country_laws_119


class CountryLaw119Spider(scrapy.Spider):
    name = 'country_laws_119'
    allowed_domains = ['chinaclear.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.chinaclear.cn/zdjs/xgsdt/center_list_one_{}.shtml'
        start_url = ['http://www.chinaclear.cn/zdjs/xgsdt/center_list_one.shtml']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://www.chinaclear.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 15):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="pageTabContent"]/ul//li/a/@href').extract()
        law_title = response.xpath('//div[@class="pageTabContent"]/ul//li/a/@title').extract()
        law_time = response.xpath('//div[@class="pageTabContent"]/ul//li/span/text()').extract()

        # 补充
        law_url_list_supplyment = response.xpath('//div[@class="title"]/h2/a/@href').extract()
        for i in range(len(law_url_list_supplyment)):
            if re.search(r'\../../', law_url_list_supplyment[i]):
                law_url = re.sub('../../', '/', law_url_list_supplyment[i])
                tmpurl_supplyment = 'http://www.chinaclear.cn' + law_url
                law_url_list.append(tmpurl_supplyment)

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
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中国证券登记结算有限责任公司"
        item["legalCategory"] = "中国结算-公司动态"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="zoom"]').extract_first()
            fujian = response.xpath('//div[@class="content"]//a[contains(@href,"http")]/@href').extract()
            fujian_name = response.xpath('//div[@class="content"]//a[contains(@href,"http")][@href]').xpath('string(.)').extract()

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
