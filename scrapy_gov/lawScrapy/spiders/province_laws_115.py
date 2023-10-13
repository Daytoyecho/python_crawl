# -*- coding:utf-8 -*-
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from selenium import webdriver
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
seleniumLogger.setLevel(logging.WARNING)
option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_experimental_option('excludeSwitches', ['enable-logging'])
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')

# scrapy crawl province_laws_115


class ProvinceLaw115Spider(scrapy.Spider):
    name = 'province_laws_115'
    allowed_domains = ['xa.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.xa.gov.cn/gk/zcfg/gz/{}.html"
        start_url = ['http://www.xa.gov.cn/gk/zcfg/gz/1.html']

        for i in range(2, 6):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)
        law_url_list = []
        law_title = []
        tmp_text = []
        for i in driver.find_elements_by_xpath('//p[@class="title"]/a'):
            law_url_list.append(i.get_attribute('href'))
            law_title.append(i.text)

        for i in driver.find_elements_by_xpath('//p[@class="time"]'):
            tmp_text.append(i.text)
        driver.quit()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "text": tmp_text[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "西安市"
        item["legalCategory"] = "西安市政府-规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        if re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']):
            tmp_time = re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']).group(1)
            item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time.strip(), "%Y年%m月%d日"))
        else:
            item["legalPublishedTime"] = ""

            # 处理文号
        if re.search(r'(西安市人民政府.*?[0-9]{0,4}.*?号)', response.meta['text']):
            item["legalDocumentNumber"] = re.search(r'(西安市人民政府.*?[0-9]{0,4}.*?号)', response.meta['text']).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="article"]').extract_first()
            fujian = response.xpath('//*[@id="article"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="article"]//a[@href]').xpath('string(.)').extract()

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
