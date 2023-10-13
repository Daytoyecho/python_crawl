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
# option.add_extension(tools.proxy_auth_plugin_path)
option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument('disable-blink-features=AutomationControlled')
# scrapy crawl province_laws_121


class ProvinceLaw121Spider(scrapy.Spider):
    name = 'province_laws_121'
    allowed_domains = ['xxgk.jl.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://infogate.jl.gov.cn/govsearch/jsonp/zf_jd_list.jsp?page={}&lb=134657&callback=result&sword=&searchColumn=all&searchYear=all&pubURL=http%3A%2F%2Fxxgk.jl.gov.cn%2F&SType=1&searchYear=all&pubURL=&SType=1&channelId=134657&_=1653378851138"
        start_url = []
        for i in range(40, 179):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            time.sleep(4)
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        str = response.text[67:-4]
        str = json.loads(str)
        for i in str['data']:
            tmpurl = i['puburl']
            law_title = i['title']
            law_time = i['tip']['dates']
            law_number = i['tip']['filenum']
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "number": law_number, "times": law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "吉林省"
        item["legalCategory"] = "吉林省政府-政府信息公开基础平台"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])
        item["legalPublishedTime"] = response.meta["times"]

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
            time.sleep(3)
            content = driver.find_element_by_xpath('//*[@id="zoom"]').get_attribute('outerHTML')
            for i in driver.find_elements_by_xpath('//*[@id="zoom"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)

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
