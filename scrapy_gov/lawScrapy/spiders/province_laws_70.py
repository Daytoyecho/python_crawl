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
# scrapy crawl province_laws_70


class ProvinceLaw70Spider(scrapy.Spider):
    name = 'province_laws_70'
    allowed_domains = ['chengdu.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        with open("lawScrapy/spiders/p70.txt", 'r', encoding="utf-8") as f:
            data = f.read()
        start_url = re.findall(r"detail\.action\?id=([0-9]+)", data)
        law_title = re.findall(r'<span class="s2">• ([^<>]+?)<', data)
        law_time = re.findall(r'<span class="s4">([^<>]+?)<', data)

        header = deepcopy(tools.header)
        header['Referer'] = 'http://gk.chengdu.gov.cn/govInfo/'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(len(start_url)):
            tmpurl = "http://gk.chengdu.gov.cn/govInfo/detail.action?id={}&tn=6".format(str(start_url[i]))
            time.sleep(0.2)
            yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "四川省"
        item["legalCategory"] = "成都市政府-规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="myFont"]').extract_first()
            fujian = response.xpath('//*[@id="myFont"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="myFont"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//*[@class="l1"]/b[contains(text(),"文")]/../text()').extract_first()
            if re.search("号", wenhao):
                item["legalDocumentNumber"] = wenhao

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
