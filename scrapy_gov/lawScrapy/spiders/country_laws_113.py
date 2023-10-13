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
# scrapy crawl country_laws_113


class CountryLaw113Spider(scrapy.Spider):
    name = 'country_laws_113'
    allowed_domains = ['szse.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = 'http://www.szse.cn/aboutus/trends/news/index_{}.html'
        start_url = ['http://www.szse.cn/aboutus/trends/news/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(1, 158):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        text = response.xpath('//body').extract_first()
        law_url_list = re.findall(r"var curHref = '\.([^']+?)'", text)
        law_title = re.findall(r"//var curTitle = '([^']+?)'", text)
        law_time = response.xpath('//span[@class="time"]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl = "http://www.szse.cn/aboutus/trends/news" + law_url_list[i]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "深圳证券交易所"
        item["legalCategory"] = "深交所本所要闻更新"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@id="desContent"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="desContent"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@id="desContent"]').extract_first()
            # if re.search("〔", response.xpath('//div[@id="desContent"]/p[1]').extract_first()):
            #     tmp = re.search("〔", response.xpath('//div[@id="desContent"]/p[1]').xpath('string(.)').extract()).group(1)
            #     if len(tmp) < 20:
            #         item["legalDocumentNumber"] = tools.clean(tmp)

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
