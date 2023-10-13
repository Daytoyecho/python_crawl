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
# scrapy crawl country_laws_85


class CountryLaw85Spider(scrapy.Spider):
    name = 'country_laws_85'
    allowed_domains = ['mee.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.mee.gov.cn/zcwj/bgtwj/han/index_{}.shtml'
        start_url = ['https://www.mee.gov.cn/zcwj/bgtwj/han/index.shtml']

        for i in range(1, 34):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="bd mobile_list"]//ul//li/a/@href').extract()
        law_title = response.xpath('//div[@class="bd mobile_list"]//ul//li/a/text()').extract()
        law_time = response.xpath('//span[@class="date"]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = tools.getpath(law_url_list[i], response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国生态环境部"
        item["legalCategory"] = "中华人民共和国生态环境部-政策文件-办公室文件-函"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            item["legalDocumentNumber"] = response.xpath('//li[@class="last"]/div[contains(text(),"号")]/text()').extract_first()
            fujian = response.xpath('//div[@class="content_body"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="content_body"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@class="content_body"]').extract_first()

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
