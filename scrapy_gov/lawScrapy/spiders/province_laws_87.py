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
# scrapy crawl province_laws_87


class ProvinceLaw87Spider(scrapy.Spider):
    name = 'province_laws_87'
    allowed_domains = ['henan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://wjbb.sft.henan.gov.cn/regulatory/viewQueryAll.do?offset={}&cdid=402881fa2d1738ac012d173a60930017"

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(512):
            yield scrapy.Request(start_url.format(str(i*15)), self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        url_list = response.xpath('//*[@class="serListCon"]//a/@href').extract()
        title_list = response.xpath('//*[@class="serListCon"]//a/@title').extract()
        time_list = response.xpath('//*[@class="serListCon"]//span/text()').extract()

        for i in range(len(url_list)):
            tmpurl = url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = title_list[i]
            law_time = time_list[i]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "河南省"
        item["legalCategory"] = "河南省政府-规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])[1:-1]
        time.sleep(2)
        wenhao = re.search(r'[）\)]([\s\S]+?)[\(（]', response.meta['title'][::-1])
        if wenhao:
            item["legalDocumentNumber"] = wenhao.group(1)[::-1]
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        tools.xaizai_not_html_zw(pdf_name, response.body)
        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.url)
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
