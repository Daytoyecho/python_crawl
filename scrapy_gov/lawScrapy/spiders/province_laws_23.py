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
from copy import deepcopy
urllibLogger.setLevel(logging.WARNING)
seleniumLogger.setLevel(logging.WARNING)
option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_experimental_option('excludeSwitches', ['enable-logging'])
option.add_argument('--no-sandbox')
option.add_argument('--disable-dev-shm-usage')

# scrapy crawl province_laws_23


class ProvinceLaw23Spider(scrapy.Spider):
    name = 'province_laws_23'
    allowed_domains = ['cq.gov.cn']
    count = 0
    url_list = []

    def start_requests(self):
        start_url = 'http://www.cq.gov.cn/govserver/tors/serchByIndustry.html'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        base = {
            'industry': '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19',
            'level': '2',
            'pageIndex': '1',
            'pageSize': '15',
            'type': '',
        }

        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.cq.gov.cn'
        header['Referer'] = 'http://www.cq.gov.cn/ykbzt/zcztc/list.html?level=2'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

       # 最后一页没东西
        for i in range(1, 41):
            tmp = deepcopy(base)
            tmp['pageIndex'] = str(i)
            self.count += 1
            print(self.count)
            yield scrapy.FormRequest(url=start_url, formdata=tmp, callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['data']['dataList']

        for item in data_list:
            id = item['policyId']
            law_url = "http://www.cq.gov.cn/ykbzt/zcztc/detail.html?policyId="+str(id)
            law_title = item['policyName']
            law_time = item['createTime']
            if law_url not in self.url_list:
                yield scrapy.Request(law_url, callback=self.parse_article, meta={"title": law_title, 'time': law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url

        item["legalProvince"] = "重庆市"
        item["legalCategory"] = "重庆市政府-政策"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        driver = webdriver.Chrome(chrome_options=option)
        driver.get(response.url)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = driver.find_element_by_xpath('//div[@class="lf-box-content"]').get_attribute('outerHTML')
            for i in driver.find_elements_by_xpath('//div[@class="lf-box-content"]//a'):
                fujian.append(i.get_attribute('href'))
                fujian_name.append(i.text)

            tmpn = driver.find_element_by_xpath('//td[@class="td-w35"]/div[@class="li-zh"]/span').text
            if tmpn:
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
