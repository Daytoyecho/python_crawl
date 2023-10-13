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
# scrapy crawl country_laws_126


class CountryLaw126Spider(scrapy.Spider):
    name = 'country_laws_126'
    allowed_domains = ['sac.net.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.sac.net.cn/flgz/zlgz/index_{}.html'
        start_url = ['https://www.sac.net.cn/flgz/zlgz/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "https://www.sac.net.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 10):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)
        law_url_list = []
        law_title = []

        for i in driver.find_elements_by_xpath('//table[@class="mar_cen gl_list"]/tbody//tr//td[1]/a'):
            law_url_list.append(i.get_attribute('href'))
            law_title.append(i.get_attribute('title'))
        driver.quit()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中国证券业协会"
        item["legalCategory"] = "中国证券业协会-自律规则"

        ###时间待改正
        item["legalPolicyName"] = ''


        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = ""
            try:
                content = driver.find_element_by_xpath('//*[@class="TRS_Editor"]').get_attribute('outerHTML')
            except:
                pass
            if not content:
                try:
                    content = driver.find_element_by_xpath('//*[@class="TRS_PreAppend"]').get_attribute('outerHTML')
                except:
                    pass

            for i in driver.find_elements_by_xpath('//td[@class="xl_cen"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)
            driver.quit()

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
