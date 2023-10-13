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

# scrapy crawl province_laws_129


class ProvinceLaw129Spider(scrapy.Spider):
    name = 'province_laws_129'
    allowed_domains = ['gxzf.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = 'http://www.gxzf.gov.cn/igs/front/search/list.html?index=file2-index-alias&type=governmentdocuments&pageNumber={}&pageSize=10&filter[AVAILABLE]=true&filter[fileNum-like]=&filter[Effectivestate]=&filter[fileYear]=&filter[fileYear-lte]=&filter[FileName,DOCCONTENT,fileNum-or]=&siteId=14&filter[SITEID]=3&orderProperty=PUBDATE&orderDirection=desc'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 801):
            time.sleep(2)
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['page']['content']

        for i in data_list:

            law_url = i['DOCPUBURL']
            law_title = i['DOCTITLE']
            law_time = i['PUBDATE']
            law_number = i['fileNum']
            law_url = tools.getpath(law_url, response.url)
            self.count += 1
            print(self.count)
            if law_url not in self.url_list:
                yield scrapy.Request(law_url, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "广西壮族自治区"
        item["legalCategory"] = "广西壮族自治区政府-文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'][:10])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[contains(@class,"TRS_UEDITOR")]').extract_first()
            fujian = response.xpath('//*[contains(@class,"TRS_UEDITOR")]//a/@href').extract()
            fujian_name = response.xpath('//*[contains(@class,"TRS_UEDITOR")]//a[@href]').xpath('string(.)').extract()

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
