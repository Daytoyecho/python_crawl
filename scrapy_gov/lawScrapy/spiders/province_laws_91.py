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

# scrapy crawl province_laws_91


class ProvinceLaw91Spider(scrapy.Spider):
    name = 'province_laws_91'
    allowed_domains = ['ln.gov.cn']
#-------------------------------------------------------------#
    url_list = []

    def start_requests(self):

        start_url = ['http://jrjg.ln.gov.cn/zfxxgk_146759/fdzdgknr/lzyj/szfgz/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://jrjg.ln.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//ul[@class="xxgk_rulzd"]//li/a/@href').extract()
        law_title = response.xpath('//ul[@class="xxgk_rulzd"]//li/a/text()').extract()
        law_time = response.xpath('//ul[@class="xxgk_rulzd"]//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "辽宁省"
        item["legalCategory"] = "辽宁省地方金融监督管理局-省政府规章"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        item["legalDocumentNumber"] = "辽宁省人民政府令第336号"

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            fujian = response.xpath('//div[@class="TRS_Editor"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract()
            #-------------------------------------------------------------#

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
