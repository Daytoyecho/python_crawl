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
# option.add_argument('headless')
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')
option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument('disable-blink-features=AutomationControlled')
# scrapy crawl province_laws_13


class ProvinceLaw13Spider(scrapy.Spider):
    name = 'province_laws_13'
    allowed_domains = ['shmh.gov.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):
        with open("lawScrapy/spiders/p13.txt", 'r', encoding="utf-8") as f:
            text = f.read()

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        law_url_list = re.findall(r'<a href="([^"]+?)"', text)
        law_title = re.findall(r'" title="([^"]+?)"', text)
        law_time = re.findall(r'<span class="time">([^<>]+?)<', text)

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], "https://www.shmh.gov.cn/shmh/tzzc/index.html")
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if item["legalUrl"] in self.url_list:
            0/0
        item["legalProvince"] = "上海市"
        item["legalCategory"] = "上海市闵行区人民政府-政府信息公开制度"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

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
        time.sleep(10)
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = driver.find_element_by_xpath('//div[@class="Article_content"]').get_attribute('outerHTML')
            for i in driver.find_elements_by_xpath('//div[@class="Article_content"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)

            #########如果时间或者文号需要用到xpath或者re，请放到这儿来#########
            wenhao = ""
            try:
                wenhao = re.search(r">([^<>]+?[0-9]{4}[^<>]+?号)", content).group(1)
            except:
                pass
            if len(wenhao) < 15:
                item["legalDocumentNumber"] = tools.clean(wenhao)

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
