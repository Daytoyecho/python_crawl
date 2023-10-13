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

# scrapy crawl province_laws_105


class ProvinceLaw104Spider(scrapy.Spider):
    name = 'province_laws_105'
    allowed_domains = ['shaanxi.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = [['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbf/index_{}.html', 134],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbz/index_{}.html', 6],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbfmd/index_{}.html', 14],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbh/index_{}.html', 62],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/qt/index_{}.html', 1],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/rsxx_209/index_{}.html', 67],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szf/index_{}.html', 72],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szz/index_{}.html', 18],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szrz/index_{}.html', 134],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/sztb/index_{}.html', 46],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szh/index_{}.html', 59],
                ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/qt/index_{}.html', 1]]

        start_url = ['http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbf/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbz/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbfmd/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/szbh/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfbgtwj/qt/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/rsxx_209/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szf/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szz/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szrz/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/sztb/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/szh/',
                     'http://www.shaanxi.gov.cn/zfxxgk/fdzdgknr/zcwj/szfwj/qt/']

        for item in base:
            for i in range(1, item[1]):
                start_url.append(item[0].format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//*[contains(@class,"gov-item")]/li')

        for item in data_list:
            tmpurl = item.xpath('./div/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./div/a/@title').extract_first()
            law_time = item.xpath('./span[2]/text()').extract_first()
            law_number = item.xpath('./span[1]/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "陕西省"
        item["legalCategory"] = "陕西省政府-其他文件"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):

            content = response.xpath('//*[contains(@class,"TRS_UEDITOR")]').extract_first()
            if not content:
                content = response.xpath('//*[@id="doc_left"]').extract_first()
            fujian = response.xpath('//*[@id="doc_left"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="doc_left"]//a[@href]').xpath('string(.)').extract()
            item['legalContent'] = content
            content = re.sub(r'<div class="code f-tac"[\s\S]+?</div>', "", content)
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
