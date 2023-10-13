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
# scrapy crawl province_laws_76


class ProvinceLaw76Spider(scrapy.Spider):
    name = 'province_laws_76'
    allowed_domains = ['ah.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        with open("lawScrapy/spiders/p76.txt", 'r', encoding="utf-8") as f:
            text = f.read()
        url_list = re.findall(r'<a href="([^"]+)', text)
        title_list = re.findall(r'target="_blank">([\s\S]+?)</a>', text)
        time_list = re.findall(r'<span class="date">([\s\S]+?)</span>', text)
        for i in range(len(url_list)):
            tmpurl = url_list[i]
            law_title = title_list[i]
            law_time = time_list[i]
            tmpurl = tools.getpath(tmpurl, "http://ahjr.ah.gov.cn/public/column/6595751?type=4&action=list&nav=3&sub=&catId=6716900")
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            tools.MyException("与数据库重复")
        item["legalProvince"] = "安徽省"
        item["legalCategory"] = "安徽省地方金融监督管理局-规范性文件立改废"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//*[@class="div_table_suoyin"]/table[1]/tbody/tr[6]/td[1]/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = tools.clean(wenhao)

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
