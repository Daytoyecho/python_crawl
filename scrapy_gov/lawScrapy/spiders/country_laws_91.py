# -*- coding:utf-8 -*-
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

# scrapy crawl country_laws_91


class CountryLaw91Spider(scrapy.Spider):
    name = 'country_laws_91'
    allowed_domains = ['chinatax.gov.cn']
    count = 0
    url_list = []

    def start_requests(self):
        start_url = 'http://www.chinatax.gov.cn/api/query?siteCode=bm29000fgk&tab=all&key=9A9C42392D397C5CA6C1BF07E2E0AA6F'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')

        self.url_list = [item['legalUrl'] for item in res]

        base = {
            'timeOption': '0',
            'page': '1',
            'pageSize': '10',
            'keyPlace': '0',
            'sort': 'dateDesc',
            'qt': '*'
        }
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.chinatax.gov.cn'
        header['Referer'] = 'http://www.chinatax.gov.cn/chinatax/n810341/n810825/index.html?title='
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

       # 最后一页没东西
        for i in range(1, 488):
            tmp = deepcopy(base)
            tmp['page'] = str(i)
            time.sleep(0.1)
            yield scrapy.FormRequest(url=start_url, formdata=tmp, callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['resultList']

        for item in data_list:
            tmpurl = item['url']
            law_title = item['dreTitle']
            law_time = item['publishTime']
            law_document_number = item['customHs']['DOCNOVAL']
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, callback=self.parse_article, meta={"title": law_title, 'time': law_time, 'documentNumber': law_document_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if item["legalUrl"] in self.url_list:
            0/0
        item["legalProvince"] = "中华人民共和国国家税务总局"
        item["legalCategory"] = "税务总局-税收政策最新文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y-%m-%d %H:%M:%S"))
        item["legalDocumentNumber"] = tools.clean(response.meta['documentNumber'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="fontzoom"]').extract_first()
            fujian = response.xpath('//div[contains(@class,"container")]//a/@href').extract()
            fujian_name = response.xpath('//div[contains(@class,"container")]//a[@href]').xpath('string(.)').extract()

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
