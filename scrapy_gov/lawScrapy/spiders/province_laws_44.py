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
# scrapy crawl province_laws_44


class ProvinceLaw44Spider(scrapy.Spider):
    name = 'province_laws_44'
    allowed_domains = ['hangzhou.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = ["http://www.hangzhou.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=300&perpage=100",
                     "http://www.hangzhou.gov.cn/module/jpage/dataproxy.jsp?startrecord=301&endrecord=410&perpage=300"]

        baseform = 'col=1&appid=1&webid=149&path=%2F&columnid=1229063381&sourceContentType=1&unitid=7123773&webname=%E6%9D%AD%E5%B7%9E%E5%B8%82%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C%E9%97%A8%E6%88%B7%E7%BD%91%E7%AB%99&permissiontype=0'
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.hangzhou.gov.cn'
        header['Referer'] = 'http://www.hangzhou.gov.cn/col/col1229063381/index.html?uid=7123773&pageNum=4'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('target="_blank" href="([^"]+?)"', response.text)
        law_title_list = re.findall('<a title="([^"]+?)"', response.text)
        law_time_list = re.findall('</a><b>([^<>]+?)</b>', response.text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "杭州市"
        item["legalCategory"] = "杭州市政府-市政府行政规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//*[@class="xxgkinfo"]//tr[2]/td[2]/text()').extract_first()
            if tmpn and re.search(r'\d', tmpn):
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
