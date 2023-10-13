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
# scrapy crawl province_laws_57


class ProvinceLaw57Spider(scrapy.Spider):
    name = 'province_laws_57'
    allowed_domains = ['nanjing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = "https://www.nanjing.gov.cn/xxgkn/fggz/gz/index_{}.html"
        start_url = ["https://www.nanjing.gov.cn/xxgkn/fggz/gz/index.html"]

        for i in range(1, 8):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url.format(i), self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//ul[@class="universal_overview_con"]/li')

        for item in data_list:
            tmpurl = item.xpath('./span[2]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./span[2]/a/@title').extract_first()
            law_time = item.xpath('./span[3]/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1.5)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江苏省"
        item["legalCategory"] = "南京市政府-规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[contains(@class,"TRS_UEDITOR")]').extract_first()
            fujian = response.xpath('//*[@class="t1"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="t1"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@class="wenZhang"]').extract_first()
                content = re.sub(r'<div class="con_f">[\s\S]+?</div>', '', content)

            tmpn = response.xpath('//*[@class="t1"]//tr[5]/td[2]/text()').extract_first()
            if tmpn and re.search(r'\d', tmpn):
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
