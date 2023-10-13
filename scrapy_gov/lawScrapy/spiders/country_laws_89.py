# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_89


class CountryLaw89Spider(scrapy.Spider):
    name = 'country_laws_89'
    allowed_domains = ['sasac.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://www.sasac.gov.cn/n2588035/n2588320/n2588335/index_2603340_{}.html'
        start_url = ['http://www.sasac.gov.cn/n2588035/n2588320/n2588335/index.html']

        for i in range(17, 0, -1):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        if not re.search("index_2603340_", response.url):
            law_url_list = response.xpath('//div[@class="zsy_conlist"]/ul/span/li/a/@href').extract()
            law_title = response.xpath('//div[@class="zsy_conlist"]/ul/span/li/a/@title').extract()
            law_time = response.xpath('//span[@id="comp_2603340"]/li/span/text()').extract()
            for i in range(len(law_url_list)):
                tmpurl = tools.getpath(law_url_list[i], response.url)
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)
        else:
            law_url_list = response.xpath('//li/a/@href').extract()
            law_title = response.xpath('//li/a/@title').extract()
            law_time = response.xpath('//li/span/text()').extract()
            for i in range(len(law_url_list)):
                tmpurl = tools.getpath(law_url_list[i], response.url)
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "国务院国有资产监督管理委员会"
        item["legalCategory"] = "国资委-政策发布"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = response.meta['time'][1:-1]

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@class="zsy_comain"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="zsy_comain"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@class="zsy_comain"]').extract_first()

            item["legalDocumentNumber"] = ""
            tmp = response.xpath('//div[@class="zsy_comain"]/p[2]').xpath('string(.)').extract_first()
            if not tmp:
                tmp = response.xpath('//div[@class="zsy_comain"]/div[2]/text()').extract_first()
            if re.search(r"\[[0-9]{4}\]", tmp) or re.search(r"第[0-9]+号", tmp):
                item["legalDocumentNumber"] = tmp.replace(' ', '').replace('\n', '').replace('\r', '')
            else:
                try:
                    item["legalDocumentNumber"] = re.search(r'>([^<]+?\[[0-9]{4}\][^<]+?号)<', content).group(1)
                except:
                    pass
            if not item["legalDocumentNumber"]:
                try:
                    item["legalDocumentNumber"] = re.search(r'>([^<]+?〔[0-9]{4}〕[^<]+?号)<', content).group(1)
                except:
                    pass

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
