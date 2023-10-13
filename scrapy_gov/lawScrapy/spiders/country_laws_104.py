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
# scrapy crawl country_laws_104


class CountryLaw104Spider(scrapy.Spider):
    name = 'country_laws_104'
    allowed_domains = ['sse.com.cn']
    url_list = []
    count = 0

    def start_requests(self):
        BASEURL = "http://www.sse.com.cn/home/search/?webswd=%E5%85%AC%E5%BC%80%E5%BE%81%E6%B1%82%E6%84%8F%E8%A7%81"
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        with open("lawScrapy/spiders/c104.json", 'r', encoding="utf-8") as f:
            data = json.load(f)

        for i in data:
            for item in i:
                url = item["CURL"]
                tmpurl = tools.getpath(url, BASEURL)
                law_title = item["CTITLE_TXT"]
                law_time = item["CRELEASETIME"]
                self.count += 1
                print(self.count)
                if tmpurl not in self.url_list:
                    yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "上海证券交易所"
        item["legalCategory"] = "上交所--公开征求意见"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[contains(@class,"article-infor")]//a/@href').extract()
            fujian_name = response.xpath('//div[contains(@class,"article-infor")]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//*[@class="allZoom"]').extract_first()
            if not content:
                content = "".join(response.xpath('//div[contains(@class,"content_area_article")]//p').extract())
            if re.search(r"(上[\s\S]{1,8}[0-9]{4}[\s\S]{1,8}号)", content):
                item["legalDocumentNumber"] = re.search(r"(上[\s\S]{1,8}[0-9]{4}[\s\S]{1,8}号)", content).group(1)

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
