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

# scrapy crawl country_laws_121


class CountryLaw121Spider(scrapy.Spider):
    name = 'country_laws_121'
    allowed_domains = ['chinaclear.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):
        base = [['http://www.chinaclear.cn/zdjs/fzhgl/law_flist_{}.shtml', 1],
                ["http://www.chinaclear.cn/zdjs/ffl/law_tlist_{}.shtml", 3],
                ["http://www.chinaclear.cn/zdjs/fsfjs/law_tlist_{}.shtml", 3],
                ["http://www.chinaclear.cn/zdjs/fxzfg/law_tlist_{}.shtml", 2],
                ["http://www.chinaclear.cn/zdjs/fbmgz/law_tlist_{}.shtml", 11],
                ["http://www.chinaclear.cn/zdjs/fdjycg/law_flist_{}.shtml", 3],
                ["http://www.chinaclear.cn/zdjs/fqsyjs/law_flist_{}.shtml", 2],
                ["http://www.chinaclear.cn/zdjs/fcyrgl/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/zqfb/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/kcb/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/zqyw/law_flist_{}.shtml", 4],
                ["http://www.chinaclear.cn/zdjs/gpqq/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/rzrqyzrt/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/fswyw/law_flist_{}.shtml", 2],
                ["http://www.chinaclear.cn/zdjs/fqt/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/gzywxy/law_flist_{}.shtml", 1],
                ["http://www.chinaclear.cn/zdjs/yfzywgz/law_flist_{}.shtml", 17]
                ]

        start_url = ['http://www.chinaclear.cn/zdjs/fzhgl/law_flist.shtml',
                     "http://www.chinaclear.cn/zdjs/ffl/law_tlist.shtml",
                     "http://www.chinaclear.cn/zdjs/fsfjs/law_tlist.shtml",
                     "http://www.chinaclear.cn/zdjs/fxzfg/law_tlist.shtml",
                     "http://www.chinaclear.cn/zdjs/fbmgz/law_tlist.shtml",
                     "http://www.chinaclear.cn/zdjs/fdjycg/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/fqsyjs/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/fcyrgl/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/zqfb/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/kcb/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/zqyw/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/gpqq/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/rzrqyzrt/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/fswyw/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/fqt/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/gzywxy/law_flist.shtml",
                     "http://www.chinaclear.cn/zdjs/yfzywgz/law_flist.shtml"
                     ]
        for item in base:
            for i in range(2, item[1]+1):
                start_url.append(item[0].format(str(i)))
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="pageTabContent"]/ul//li/a/@href').extract()
        law_title = response.xpath('//div[@class="pageTabContent"]/ul//li/a/@title').extract()
        law_time = response.xpath('//div[@class="pageTabContent"]/ul//li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中国证券登记结算有限责任公司"
        item["legalCategory"] = "中国结算-业务规则"
        #-------------------------------------------------------------#

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if re.search(r"【第[0-9]+?号令】", item["legalPolicyName"]):
            item["legalDocumentNumber"] = re.search(r"(【第[0-9]+?号令】)", item["legalPolicyName"]).group(1)
        elif re.search(r"[\(（][^\(\)]+?\d+号", item["legalPolicyName"]):
            item["legalDocumentNumber"] = re.search(r"[\(（]([^\(\)]+?第\d+号)", item["legalPolicyName"]).group(1)
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="zoom"]').extract_first()
            fujian = response.xpath('//div[@class="content"]//a[contains(@href,"http")]/@href').extract()
            fujian_name = response.xpath('//div[@class="content"]//a[contains(@href,"http")][@href]').xpath('string(.)').extract()

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
