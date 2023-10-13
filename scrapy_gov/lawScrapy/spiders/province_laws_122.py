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
# scrapy crawl province_laws_155


class ProvinceLaw122Spider(scrapy.Spider):
    name = 'province_laws_122'
    allowed_domains = ['xxgk.jl.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "https://was.jl.gov.cn/was5/web/gov/szfgz/response_szf_guizhang.jsp?type=guizhang&callback=result&pageIndex={}&pageSize=10&keyWord=&keyWordType=all&_=1653381584585"
        start_url = []
        for i in range(1, 13):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        str = response.text[7:-2]
        str = json.loads(str)
        for i in str['data']:
            tmpurl = i['docpuburl']
            law_title = i['doctitle']
            law_number = i['docabstract']
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "吉林省"
        item["legalCategory"] = "吉林省政府-规章库"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        title_sub = tools.clean(response.meta['number'])

        number = re.search(r"[\(（]?[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日?(.+?号)", title_sub).group(1)
        item["legalDocumentNumber"] = number
        times = re.search(r"[\(（]?([0-9]{4}年[0-9]{1,2}月[0-9]{1,2})日?", title_sub).group(1)
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(times, "%Y年%m月%d"))

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            driver = webdriver.Chrome(chrome_options=option)
            driver.get(response.url)
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            time.sleep(1)
            content = driver.find_element_by_xpath('//*[@id="zoom"]').get_attribute('outerHTML')
            for i in driver.find_elements_by_xpath('//*[@id="zoom"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)
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
