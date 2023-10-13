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


class ProvinceLaw155Spider(scrapy.Spider):
    name = 'province_laws_155'
    allowed_domains = ['nx.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "https://www.nx.gov.cn/zwgk/zfxxgkzd/list_{}.html"
        start_url = ['https://www.nx.gov.cn/zwgk/zfxxgkzd/']
        for i in range(1, 3):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//ul[@class="commonList_dot"]/li')

        for item in data_list:

            tmpurl = item.xpath('./a/@href').extract_first()
            law_title = item.xpath('./a/text()').extract_first()
            #law_time = item.xpath('./span/text()').extract_first()
            # law_number = item.xpath('./div/p[7]/span[2]/text()').extract_first()

            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "宁夏回族自治区"
        item["legalCategory"] = "宁夏回族自治区政府-政府信息公开制度"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            print('\n')
            print(response.url)
            content = response.xpath('//div[@id="ofdneed"]').extract_first()
            fujian = response.xpath('//div[@id="ofdneed"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="ofdneed"]//a[@href]').xpath('string(.)').extract()
            # ########如果时间或者文号需要用到xpath或者re，请放到这儿来#########
            try:
                times = response.xpath('//span[@id="info_released_dtime"]/text()').extract_first()
                print('\n' + times)
                time.strftime("%Y-%m-%d", time.strptime(times.strip(), "%Y-%m-%d %H:%M:%S"))
                item["legalPublishedTime"] = times
                item["legalDocumentNumber"] = response.xpath('//div[@id="info_subtitle"]/text()').extract_first()
                print(item["legalDocumentNumber"])
            except:
                item["legalPublishedTime"]= response.xpath('//div[@class="nx-conmtab2 clearfix"]/p[6]/span[2]/text()').extract_first()
                item["legalDocumentNumber"] = response.xpath('//div[@class="nx-conmtab2 clearfix"]/p[7]/span[2]/text()').extract_first()

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
