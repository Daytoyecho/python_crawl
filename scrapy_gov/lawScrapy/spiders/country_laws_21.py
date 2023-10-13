# -*- coding:utf-8 -*-
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
# scrapy crawl country_laws_21


class CountryLaw21Spider(scrapy.Spider):
    name = 'country_laws_21'
    allowed_domains = ['most.gov.cn']
    url_list = []
    wrong = 0
    count = 0

    def start_requests(self):
        start_url = ['http://www.most.gov.cn/satp/kjzc/kjjl/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        law_url_list = response.xpath('//div[@class="list-main"]/ul/li/a/@href').extract()
        law_title = response.xpath('//div[@class="list-main"]/ul/li/a/text()').extract()
        law_time = response.xpath('//div[@class="list-main"]/ul/li/span/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        if re.search(r'/404\.', response.url) or response.url == "http://www.most.gov.cn/index.html":
            print("页面不存在")
            self.wrong += 1
            print("*****", self.wrong, "*****")
            0/0

        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国科学技术部"
        item["legalCategory"] = "科学技术部-科技政策科技奖励"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            if response.xpath('//div[@class="xxgk_detail_head"]//tr[4]/td[2]/text()').extract_first():
                item["legalDocumentNumber"] = response.xpath('//div[@class="xxgk_detail_head"]//tr[4]/td[2]/text()').extract_first()
            else:
                tmpn = response.xpath('//div[@class="wrap"]/table[1]//table[1]//tr[4]/td[2]/text()').extract_first()
                if tmpn:
                    item["legalDocumentNumber"] = tools.clean(tmpn)

            content = response.xpath('//*[@id="Zoom"]').extract_first()
            fujian = response.xpath('//*[@id="Zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="Zoom"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@id="UCAP-CONTENT"]').extract_first()
                fujian = response.xpath('//*[@id="UCAP-CONTENT"]//a/@href').extract()
                fujian_name = response.xpath('//*[@id="UCAP-CONTENT"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[@id="fontzoom"]').extract_first()
                fujian = response.xpath('//div[@id="fontzoom"]//a/@href').extract()
                fujian_name = response.xpath('//div[@id="fontzoom"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@id="zoom"]').extract_first()
                fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
                fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[@class="pages_content"]').extract_first()
                fujian = response.xpath('//div[@class="pages_content"]//a/@href').extract()
                fujian_name = response.xpath('//div[@class="pages_content"]//a[@href]').xpath('string(.)').extract()
            # if not content:
            #     content = response.xpath('//div[@id="xq"]').extract_first()
            #     fujian = response.xpath('//div[@id="xq"]//a/@href').extract()
            #     fujian_name = response.xpath('//div[@id="xq"]//a[@href]').xpath('string(.)').extract()
            # if not content:
            #     content = response.xpath('//div[@class="wrap"]').extract_first()
            #     fujian = response.xpath('//div[@class="wrap"]//a/@href').extract()
            #     fujian_name = response.xpath('//div[@class="wrap"]//a[@href]').xpath('string(.)').extract()

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
