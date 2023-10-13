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

# ########使用selenium请解注释下面这些话##########################
# from selenium import webdriver
# from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
# seleniumLogger.setLevel(logging.WARNING)
# option = webdriver.ChromeOptions()
# option.add_argument('headless')
# option.add_experimental_option('excludeSwitches', ['enable-logging'])
# option.add_argument('--no-sandbox')
# option.add_argument('--disable-dev-shm-usage')
# -------------------------------------------------------------#

# ########改三个数字和一个过滤域名，下面的注释是为了方便复制粘贴#####
# scrapy crawl province_laws_155


class ProvinceLaw159_4Spider(scrapy.Spider):
    name = 'province_laws_159_4'
    allowed_domains = ['yinchuan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.yinchuan.gov.cn/xxgk/zcwj/qtzfwj/zzqwj/index_{}.html"
        start_url = ['http://www.yinchuan.gov.cn/xxgk/zcwj/qtzfwj/zzqwj/']
        for i in range(1, 25):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//tbody/tr')

        for item in data_list:

            tmpurl = item.xpath('.//td[@class="xxgk-table-td-1"]/a/@href').extract_first()
            law_title = item.xpath('.//td[@class="xxgk-table-td-1"]/a/text()').extract_first()
            law_time = item.xpath('.//td[@class="xxgk-table-td-5"]/text()').extract_first()
            law_number = item.xpath('.//td[@class="xxgk-table-td-2"]/text()').extract_first()

            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title,"number": law_number,"times":law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "宁夏回族自治区"
        item["legalCategory"] = "银川市政府-其他文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        item["legalPublishedTime"] = response.meta["times"]
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            print('\n')
            print(response.url)
            content = response.xpath('//div[@class="text-con"]').extract_first()
            fujian = response.xpath('//div[@class="text-con"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="text-con"]//a[@href]').xpath('string(.)').extract()

            # ########如果时间或者文号需要用到xpath或者re，请放到这儿来#########

            # -------------------------------------------------------------#

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
