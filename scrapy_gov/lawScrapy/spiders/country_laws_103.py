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
# scrapy crawl country_laws_103


class CountryLaw103Spider(scrapy.Spider):
    name = 'country_laws_103'
    allowed_domains = ['sse.com.cn']
    url_list = []
    count = 0

    def start_requests(self):
        BASEURL = "http://www.sse.com.cn/aboutus/mediacenter/hotandd/s_index_{}.htm"
        start_url = ["http://www.sse.com.cn/aboutus/mediacenter/hotandd/",
                     "http://www.sse.com.cn/aboutus/mediacenter/hotandd/s_index.htm"]

        for i in range(2, 92):
            start_url.append(BASEURL.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//dl/dd')
        for item in data_list:
            tmpurl = item.xpath('./a/@href').extract_first()
            law_title = item.xpath('./a/@title').extract_first()
            law_time = item.xpath('./span/text()').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if item["legalUrl"] in self.url_list:
            0/0
        item["legalProvince"] = "上海证券交易所"
        item["legalCategory"] = "上交所业务热点动态更新"
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
            if not content:
                content = response.xpath('//div[@class="article-infor"]/table').extract_first()

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
