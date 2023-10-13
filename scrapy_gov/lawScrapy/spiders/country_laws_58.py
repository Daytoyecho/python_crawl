# -*- coding:utf-8 -*-
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from selenium import webdriver
import scrapy
from lawScrapy.items import LawscrapyItem
import re
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
# scrapy crawl country_laws_58


class CountryLaw58Spider(scrapy.Spider):
    name = 'country_laws_58'
    allowed_domains = ['mofcom.gov.cn']
    url_list = []
    count = 0
    wrong = 0

    def start_requests(self):
        BASEURL = 'http://www.mofcom.gov.cn/article/zhengcejd/bp/?{}'
        start_url = ['http://www.mofcom.gov.cn/article/zhengcejd/bp/']

        for i in range(2, 9):
            start_url.append(BASEURL.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in start_url:
            yield scrapy.Request(i, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//ul[@class="txtList_01"]/li')

        for item in data_list:
            tmpurl = item.xpath('./a[1]/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)

            self.count += 1
            print(self.count)
            law_title = item.xpath('./a[1]/@title').extract_first()
            law_time = item.xpath('./span/text()').extract_first()

            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.redirect, meta={"title": law_title, 'time': law_time, "proxy": tools.a_bu_yun['http']}, dont_filter=False, headers=tools.header)

    def redirect(self, response):
        if not re.search(r'}var _cofing1={href:"([^"]+)"', response.xpath('//body').extract_first()):
            yield scrapy.Request(response.url, self.parse_article, meta={"title": response.meta['title'], 'time': response.meta['time'], "proxy": tools.a_bu_yun['http']}, dont_filter=False, headers=tools.header)
        else:
            tmpurl = re.search(r'}var _cofing1={href:"([^"]+)"', response.xpath('//body').extract_first()).group(1)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": response.meta['title'], 'time': response.meta['time'], "proxy": tools.a_bu_yun['http']}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "中华人民共和国商务部"
        item["legalCategory"] = "商务部-政策解读国内贸易"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y-%m-%d %H:%M:%S"))

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@ergodic="article"]').extract_first()
            fujian = response.xpath('//*[@ergodic="article"]//a/@href').extract()
            fujian_name = response.xpath('//*[@ergodic="article"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[contains(@class,"art-con")]').extract_first()
                fujian = response.xpath('//*[contains(@class,"art-con")]//a/@href').extract()
                fujian_name = response.xpath('//*[contains(@class,"art-con")]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@class="TRS_Editor"]').extract_first()
                fujian = response.xpath('//*[@class="TRS_Editor"]//a/@href').extract()
                fujian_name = response.xpath('//*[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@id="zoom"]').extract_first()
                fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
                fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = re.search(r'<!\-\-文章正文\-\->([\s\S]+?)<script', response.xpath('//body').extract_first()).group(1)

            if not content:
                try:
                    driver = webdriver.Chrome(chrome_options=option)
                    driver.get(response.url)
                    content = driver.find_element_by_xpath('//*[contains(@class,"art-con")]').get_attribute('outerHTML')
                    for i in driver.find_elements_by_xpath('//*[contains(@class,"art-con")]//a'):
                        fujian.append(i.get_attribute('href'))
                        fujian_name.append(i.text)
                except:
                    pass

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
