# -*- coding:utf-8 -*-
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
from selenium import webdriver
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
from copy import deepcopy
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from selenium_stealth import stealth
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
# scrapy crawl province_laws_128


class ProvinceLaw128Spider(scrapy.Spider):
    name = 'province_laws_128'
    allowed_domains = ['zwgk.hlj.gov.cn']
    url_list = []
    wrong = 0
    count = 0

    def start_requests(self):

        start_url = 'https://zwgk.hlj.gov.cn/zwgk/publicInfo/searchFile?chanPath=2,214,'

        baseform = "chanId=214&chanP=2%2C214%2C&chanName=%E5%85%B6%E4%BB%96%E6%96%87%E4%BB%B6&page={}&limit=100&total=1843"

        header = deepcopy(tools.header)
        header['Referer'] = 'https://zwgk.hlj.gov.cn/zwgk/zc_list?chanId=214&chanP=2,214,&chanName=%E5%85%B6%E4%BB%96%E6%96%87%E4%BB%B6'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 19):
            time.sleep(1)
            yield scrapy.Request(start_url, body=baseform.format(str(i)), method='POST',  callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)['data']['records']
        baseu = "https://zwgk.hlj.gov.cn/zwgk/publicInfo/detail?id={}"
        for item in data:

            tmpurl = baseu.format(str(item['id']))
            law_title = item['title']
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(item['publishTime'])))
            law_number = item["fileNumber"]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request("https://fanyi.baidu.com/", self.parse_article, meta={"url": tmpurl, "title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.meta["url"]
        item["legalProvince"] = "黑龙江省"
        item["legalCategory"] = "黑龙江省政府-其他文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.meta["url"])
        fujian = []
        fujian_name = []
        if tools.isWeb(response.meta["url"]):
            driver = webdriver.Chrome(chrome_options=option)
            driver.get(response.meta["url"])
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            time.sleep(1)
            content = driver.find_element_by_xpath('//*[@class="zwnr"]').get_attribute('outerHTML')
            for i in driver.find_elements_by_xpath('//*[@class="zwnr"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)

            item['legalContent'] = content
            tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.meta["url"])
        else:
            0/0
            tools.xaizai_not_html_zw(pdf_name, response.body)
        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.meta["url"])
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
