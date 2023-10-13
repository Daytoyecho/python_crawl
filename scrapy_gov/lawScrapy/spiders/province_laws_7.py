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

# scrapy crawl province_laws_7


class ProvinceLaw7Spider(scrapy.Spider):
    name = 'province_laws_7'
    allowed_domains = ['beijing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = ['http://kw.beijing.gov.cn/col/col2386/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        url_list = re.findall(r"urls\[i\]='([^']+?)'", response.xpath('//body').extract_first())
        title_list = re.findall(r'headers\[i\]="(.*?)";year', response.xpath('//body').extract_first())
        time_list = []
        for i in re.findall(r"year\[i\]='([0-9]+)';month\[i\]='([0-9]+)';day\[i\]='([0-9]+)';", response.xpath('//body').extract_first()):
            time_list.append('-'.join(i))

        for index, url in enumerate(url_list):
            tmpurl = tools.getpath(url, response.url)
            law_title = title_list[index]
            law_time = time_list[index]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "北京市"
        item["legalCategory"] = "北京市科学技术委员会-北京市科委规范性文件"
        item["legalPolicyName"] = response.meta['title'].replace('\n', '').replace('\t', '').replace('&nbsp;', '').replace(' ', '')
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="zoom"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@id="zoom"]').extract_first()

            try:
                tmpnumber = response.xpath('//li[@class="fwzh"]/span').xpath('string(.)').extract_first().replace(" ", "").replace("\n", "")
            except:
                item["legalDocumentNumber"] = "人工审查"
            if re.search("〔", content):
                item["legalDocumentNumber"] = "人工审查"
            if re.search("[0-9]{4}", tmpnumber):
                item["legalDocumentNumber"] = tmpnumber

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
