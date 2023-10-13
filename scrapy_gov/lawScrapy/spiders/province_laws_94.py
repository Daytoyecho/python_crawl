# -*- coding:utf-8 -*-
from copy import deepcopy
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
# scrapy crawl province_laws_94


class ProvinceLaw94Spider(scrapy.Spider):
    name = 'province_laws_94'
    allowed_domains = ['hebei.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://info.hebei.gov.cn/eportal/ui?pageId=6817585&currentPage={}&moduleId=481edca469514ef1870c5c246fa77603&formKey=GOV_OPEN&columnName=EXT_STR7&relationId="

        baseform = "filter_LIKE_TITLE="
        header = deepcopy(tools.header)
        header['Content-Type'] = 'application/x-www-form-urlencoded'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 14):
            yield scrapy.Request(start_url.format(str(i)), body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//*[@class="xxgkzclbtab3"]//tr')

        for item in data_list:
            tmpurl = item.xpath('./td[2]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./td[2]/a/@title').extract_first()
            law_time = item.xpath('./td[4]/text()').extract_first()
            law_number = item.xpath('./td[3]/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "河北省"
        item["legalCategory"] = "河北省政府-冀政发"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        time.sleep(0.5)
        wenhao = response.meta['number']
        if wenhao:
            item["legalDocumentNumber"] = tools.clean(wenhao)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

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
