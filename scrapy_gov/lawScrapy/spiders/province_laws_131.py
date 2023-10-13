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
# scrapy crawl province_laws_131


class ProvinceLaw131Spider(scrapy.Spider):
    name = 'province_laws_131'
    allowed_domains = ['nanning.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = 'https://www.nanning.gov.cn/zwgk/fdzdgknr/zcwj/zfwj/xzgfxwj/index.html?fwjgdz=%E5%8D%97%E5%BA%9C%E8%A7%84&page={}'

        # res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        # self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 12):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//div[@class="zx_ml_list"]/ul//li[position()>1]')

        for item in data_list:

            tmpurl = item.xpath('./div/a/@href').extract_first()
            law_title = item.xpath('./div/a/text()').extract_first()
            law_time = item.xpath('./span[3]/text()').extract_first()
            law_number = item.xpath('./span[2]/text()').extract_first()

            tmpurl = tools.getpath(tmpurl, response.url)

            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "广西壮族自治区"
        item["legalCategory"] = "南宁市政府-行政规范性文件"
        # time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y/%m/%d"))
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="pages_content"]').extract_first()
            fujian = response.xpath('//div[@class="pages_content"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="pages_content"]//a[@href]').xpath('string(.)').extract()
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
