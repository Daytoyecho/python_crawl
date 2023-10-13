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


class ProvinceLaw156Spider(scrapy.Spider):
    name = 'province_laws_156'
    allowed_domains = ['yinchuan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.yinchuan.gov.cn/xxgk/zcwj/zfgzk/zfgzk_{}.html"
        start_url = ['http://www.yinchuan.gov.cn/xxgk/zcwj/zfgzk/zfgzk.html']
        for i in range(1, 3):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//div[@class="list-item"]')

        for item in data_list:

            tmpurl = item.xpath('./div[1]/a[1]/@href').extract_first()
            law_title = item.xpath('./div[1]/a[1]/text()').extract_first()
            title_sub = item.xpath('./div[1]/a[2]/text()').extract_first()
            number = []
            start = 0
            end = 0
            if_ = 0
            for i in range(0,len(title_sub)):
                if title_sub[i]=='第' and if_ == 0:
                    start = i
                    if_ = 1
                if title_sub[i]=='号' and if_ == 1 :
                    end = i
                    if_ = 2
            number = title_sub[start:end+1]
            #law_time = item.xpath('./span/text()').extract_first()
            law_number = number
            print(law_number)

            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title,"number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "宁夏回族自治区"
        item["legalCategory"] = "银川市政府-规章库"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)

        if tools.isWeb(response.url):
            print('\n')
            print(response.url)
            content = response.xpath('//div[@class="con-article"]').extract_first()
            fujian = response.xpath('//div[@class="con-article"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="con-article"]//a[@href]').xpath('string(.)').extract()

            # ########如果时间或者文号需要用到xpath或者re，请放到这儿来#########
            times = response.xpath('//meta[@name="PubDate"]/@content').extract_first()
            time.strftime("%Y-%m-%d", time.strptime(times.strip(), "%Y-%m-%d %H:%M"))
            item["legalPublishedTime"] = times

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