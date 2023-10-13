# -*- coding:utf-8 -*-
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from selenium import webdriver
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
seleniumLogger.setLevel(logging.WARNING)
option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_experimental_option('excludeSwitches', ['enable-logging'])
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')

# scrapy crawl province_laws_12


class ProvinceLaw12Spider(scrapy.Spider):
    name = 'province_laws_12'
    allowed_domains = ['sheitc.sh.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.sheitc.sh.gov.cn/sjxwxgwj/index_{}.html'
        start_url = ['https://www.sheitc.sh.gov.cn/sjxwxgwj/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        # for i in range(2, 10):
        #     start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)
        law_url_list = []
        law_title = []
        law_time = []

        for i in driver.find_elements_by_xpath('//ul[@class="list clearfix"]//a'):
            law_url_list.append(i.get_attribute('href'))
            law_title.append(i.text)

        for i in driver.find_elements_by_xpath('//ul[@class="list clearfix"]//h1/span'):
            law_time.append(i.text)
        driver.quit()

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
        item["legalProvince"] = "上海市"
        item["legalCategory"] = "上海市经济和信息化委员会-规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="view_cont clearfix"]').extract_first()
            fujian = response.xpath('//*[@class="view_list clearfix"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="view_list clearfix"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//h3[@class="view_tit_2 clearfix"]/p/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = tools.clean(wenhao)
            else:
                item["legalDocumentNumber"] = ""
                

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
