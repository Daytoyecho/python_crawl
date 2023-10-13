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

# scrapy crawl country_laws_94


class CountryLaw94Spider(scrapy.Spider):
    name = 'country_laws_94'
    allowed_domains = ['samr.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.samr.gov.cn/zw/wjfb/yj/index_{}.html'
        start_url = ['https://www.samr.gov.cn/zw/wjfb/yj/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 4):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="Three_zhnlist_02"]//ul//li/a/@href').extract()
        law_title = response.xpath('//div[@class="Three_zhnlist_02"]//ul//li/a/text()').extract()
    
        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国家市场监督管理总局"
        item["legalCategory"] = "国家市场监督管理总局-意见"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="Three_xilan_07"]').extract_first()
            fujian = response.xpath('//div[@class="Three_xilan_07"]//p//a/@href').extract()
            fujian_name = response.xpath('//div[@class="Three_xilan_07"]//p//a[@href]').xpath('string(.)').extract()

            tmp_time = response.xpath('//div[@class="Three_xilan01_01"]//tr[4]/td[2]//li[2]/text()').extract_first()
            if time:
                item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time.strip(), "%Y年%m月%d日"))
            else:
                item["legalPublishedTime"] = ''

            wenhao = response.xpath('//div[@class="Three_xilan01_01"]//tr[3]/td[1]//li[2]/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = tools.clean(wenhao)
            else:
                item["legalDocumentNumber"] = ""


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
