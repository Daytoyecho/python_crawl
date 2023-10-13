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
# scrapy crawl country_laws_107


class CountryLaw107Spider(scrapy.Spider):
    name = 'country_laws_107'
    allowed_domains = ['szse.cn']
    url_list = []
    count = 0

    def start_requests(self):

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        with open("lawScrapy/spiders/c107.json", 'r', encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            url = item["docpuburl"]
            law_title = item["doctitle"]
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(item["docpubtime"]/1000)))
            law_document_number = ""
            if re.search(r"〔[0-9]{4}〕", item["doccontent"]):
                law_document_number = re.search(r"(.+?〔[0-9]{4}〕.+?号)", item["doccontent"]).group(1).strip()
            if url not in self.url_list:
                yield scrapy.Request(url, self.parse_article, meta={"title": law_title, "time": law_time, "document_number": law_document_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "深圳证券交易所"
        item["legalCategory"] = "深交所-本所业务指南-股票类"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if response.meta['document_number']:
            item["legalDocumentNumber"] = response.meta['document_number']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@id="desContent"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="desContent"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@id="desContent"]').extract_first()

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
