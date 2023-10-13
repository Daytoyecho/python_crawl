# -*- coding:utf-8 -*-
from selenium_stealth import stealth
from copy import deepcopy
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
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')
option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument('disable-blink-features=AutomationControlled')
# scrapy crawl province_laws_79


class ProvinceLaw79Spider(scrapy.Spider):
    name = 'province_laws_79'
    allowed_domains = ['hubei.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.hubei.gov.cn/xxgk/hbzcjd/index_{}.shtml"
        start_url = ["http://www.hubei.gov.cn/xxgk/hbzcjd/index.shtml"]

        for i in range(20, 50):
            start_url.append(base.format(str(i)))

        header = deepcopy(tools.header)
        header['Upgrade-Insecure-Requests'] = 1
        header['Connection'] = 'keep-alive'
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            time.sleep(1)
            driver = webdriver.Chrome(chrome_options=option)
            driver.get(url)
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            data_list = []
            title_list = []
            time_list = []
            time.sleep(1)
            for i in driver.find_elements_by_xpath('//*[@class="hbgov-bfc-block"]//li/div/a[1]'):
                data_list.append(i.get_attribute('href'))
                title_list.append(i.get_attribute('title'))
            for i in driver.find_elements_by_xpath('//*[@class="hbgov-bfc-block"]//li/span'):
                time_list.append(i.text)
            driver.quit()
            for i in range(len(data_list)):
                tmpurl = data_list[i]
                tmpurl = tools.getpath(tmpurl, url)
                law_title = title_list[i]
                law_time = time_list[i][:10]
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    print(tmpurl)
                    yield scrapy.Request("http://jrj.beijing.gov.cn/zcfg/bjszcfg/", self.parse_article, meta={"url": tmpurl, "title": law_title, "time": law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.meta['url']
        item["legalProvince"] = "湖北省"
        item["legalCategory"] = "湖北省政府-政策解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.meta['url'])
        fujian = []
        fujian_name = []
        if tools.isWeb(response.meta['url']):

            driver = webdriver.Chrome(chrome_options=option)
            driver.get(response.meta['url'])
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            time.sleep(5)

            try:
                content = driver.find_element_by_xpath('//*[@class="TRS_Editor"]').get_attribute('outerHTML')
            except:
                try:
                    content = driver.find_element_by_xpath('//*[contains(@class,"TRS_UEDITOR")]').get_attribute('outerHTML')
                except:
                    pass

            for i in driver.find_elements_by_xpath('//*[@class="hbgov-article-content"]//a[@href]'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)
            driver.quit()
            item['legalContent'] = content
            tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.meta['url'])
        else:
            tools.xaizai_not_html_zw(pdf_name, response.body)
        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.meta['url'])
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
