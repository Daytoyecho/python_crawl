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
# scrapy crawl country_laws_72


class CountryLaw72Spider(scrapy.Spider):
    name = 'country_laws_72'
    allowed_domains = ['pbc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://www.pbc.gov.cn/tiaofasi/144941/144959/21895/index{}.html'
        start_url = ['http://www.pbc.gov.cn/tiaofasi/144941/144959/21895/index1.html']

        for i in range(2, 34):
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
        law_time = []
        for i in driver.find_elements_by_xpath('//*[@class="newslist_style"]/a'):
            law_url_list.append(i.get_attribute('href'))
            law_title.append(i.get_attribute('title'))

        for i in driver.find_elements_by_xpath('//span[@class="hui12"]'):
            law_time.append(i.text)

        driver.quit()

        for i in range(len(law_url_list)):
            self.count += 1
            print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中国人民银行"
        item["legalCategory"] = "中国人民银行-其他文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        try:
            if re.search(r'[\(（].*?〔[0-9]{4}〕.*?[）\)]', item["legalPolicyName"]):
                item["legalDocumentNumber"] = re.search(r'[\(（](.*?〔[0-9]{4}〕.*?)[）\)]', item["legalPolicyName"]).group(1)
            elif re.search(r'〔[0-9]{4}〕', item["legalPolicyName"]):
                item["legalDocumentNumber"] = re.search(r'(.+?号)', item["legalPolicyName"]).group(1)
        except:
            pass

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            driver = webdriver.Chrome(chrome_options=option)
            driver.get(response.url)
            for i in driver.find_elements_by_xpath('//div[@id="zoom"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)
            content = driver.find_element_by_xpath('//div[@id="zoom"]').get_attribute('outerHTML')

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
