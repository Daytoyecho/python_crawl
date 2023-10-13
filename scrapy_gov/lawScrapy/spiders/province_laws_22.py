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

# scrapy crawl province_laws_22


class ProvinceLaw22Spider(scrapy.Spider):
    name = 'province_laws_22'
    allowed_domains = ['tj.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://jrgz.tj.gov.cn/zwgk/jrzc_1/jrjzc/index_{}.html'
        start_url = ['http://jrgz.tj.gov.cn/zwgk/jrzc_1/jrjzc/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://jrgz.tj.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 27):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)
        law_url_list = []
        law_title = []

        for i in driver.find_elements_by_xpath('//div[@class="content-right-list overflow"]//li//a'):
            law_title.append(i.get_attribute('title'))
            if re.search(r'(http.*?html)', i.get_attribute('onclick')):
                law_url_list.append(re.search(r'(http.*?html)', i.get_attribute('onclick')).group(1))
        driver.quit()
        law_time = response.xpath('//p[@class="time fr"]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "天津市"
        item["legalCategory"] = "天津市地方金融监督管理局-政策"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="article_content xl-zw-info"]').extract_first()
            fujian = response.xpath('//div[@class="article_content xl-zw-info"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="article_content xl-zw-info"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//div[@class="sx-con"][contains(text(),"号")]/text()').extract_first()
            if tmpn:
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
