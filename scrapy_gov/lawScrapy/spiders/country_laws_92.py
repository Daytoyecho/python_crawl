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
urllibLogger.setLevel(logging.WARNING)


# scrapy crawl country_laws_92


class CountryLaw92Spider(scrapy.Spider):
    name = 'country_laws_92'
    allowed_domains = ['chinatax.gov.cn']
#-------------------------------------------------------------#
    count = 0
    url_list = []

    def start_requests(self):

        #########找到所有起始的列表页链接################################
        base = 'http://www.chinatax.gov.cn/chinatax/manuscriptList/n810760?_isAgg=0&_pageSize=20&_template=index&_channelName=%E6%94%BF%E7%AD%96%E8%A7%A3%E8%AF%BB&_keyWH=wenhao&page={}'
        start_url = ['http://www.chinatax.gov.cn/chinatax/manuscriptList/n810760?_isAgg=0&_pageSize=20&_template=index&_channelName=%E6%94%BF%E7%AD%96%E8%A7%A3%E8%AF%BB&_keyWH=wenhao&page=1']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "http://www.chinatax.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 30):

            start_url.append(base.format(str(i)))

        for url in start_url:
            time.sleep(0.1)
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        #########找到文章链接的父结点####################################
        data_list = response.xpath('//ul[@class="list"]//li')
        #-------------------------------------------------------------#

        for item in data_list:

            #########找到文章链接的父结点####################################
            tmpurl = item.xpath('./a/@href').extract_first()
            law_title = item.xpath('./a/text()').extract_first()
            law_time = item.xpath('./span/text()').extract_first()
            #-------------------------------------------------------------#

            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国家税务总局"
        item["legalCategory"] = "税务总局-税收政策政策解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'][1:-1])
        item["legalDocumentNumber"] = ""

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="fontzoom"]').extract_first()
            fujian = response.xpath('//div[contains(@class,"container")]//p//a/@href').extract()
            fujian_name = response.xpath('//div[contains(@class,"container")]//p//a[@href]').xpath('string(.)').extract()

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
