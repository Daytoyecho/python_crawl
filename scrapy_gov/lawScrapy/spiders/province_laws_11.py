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
# scrapy crawl province_laws_11


class ProvinceLaw11Spider(scrapy.Spider):
    name = 'province_laws_11'
    allowed_domains = ['shanghai.gov.cn']
    start_urls = ['https://www.shanghai.gov.cn/nw10800/index.html']
    url_list = []
    count = 0

    def parse(self, response, **kwargs):
        start_url = response.xpath('//*[@role="tabpanel"]/a/@href').extract()

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            tmpurl = tools.getpath(url, response.url)
            yield scrapy.Request(tmpurl, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//ul[contains(@class,"tadaty-list")]/li')

        for item in data_list:
            tmpurl = item.xpath('./a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./a/text()').extract_first()
            law_time = item.xpath('./span/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "上海市"
        item["legalCategory"] = "上海市政府-政府文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="Article_content"]').extract_first()
            fujian = response.xpath('//div[@class="Article_content"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="Article_content"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[@id="ivs_content"]').extract_first()
                fujian = response.xpath('//div[@id="ivs_content]//a/@href').extract()
                fujian_name = response.xpath('//div[@id="ivs_content]//a[@href]').xpath('string(.)').extract()

            text = tools.clean(re.sub(r"<[^<>]+?>", "", content))
            if re.search("上海[\s\S]{4,12}[0-9]+?号", text):
                item["legalDocumentNumber"] = re.search("(上海[\s\S]{4,12}[0-9]+?号)", text).group(1)
            elif re.search("沪[\s\S]{6,15}[0-9]+号", text):
                item["legalDocumentNumber"] = re.search("(沪[\s\S]{6,15}[0-9]+号)", text).group(1)
            elif re.search("〔", text):
                item["legalDocumentNumber"] = "***********"

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
