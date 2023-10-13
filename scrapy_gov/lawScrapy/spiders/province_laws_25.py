# -*- coding:utf-8 -*-
'''
广东省
广东省政府-政策法规
'''
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
# scrapy crawl province_laws_25


class ProvinceLaw25Spider(scrapy.Spider):
    name = 'province_laws_25'
    allowed_domains = ['gd.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = "http://www.gd.gov.cn/zwgk/wjk/zcfgk/index_{}.html"
        start_url = ['http://www.gd.gov.cn/zwgk/wjk/zcfgk/']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 238):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//div[@class="viewList"]//li')
        for item in data_list:
            tmpurl = item.xpath('./span[@class="til"]/a/@href').extract_first()
            law_title = item.xpath('./span[@class="til"]/a/text()').extract_first()
            law_time = item.xpath('./span[@class="time"]/text()').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "广东省"
        item["legalCategory"] = "广东省政府-政策法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            fujian = response.xpath('//div[@class="zw"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="zw"]//a[@href]').xpath('string(.)').extract()
            content = response.xpath('//div[@class="zw"]').extract_first()

            tmpn1 = ""
            try:
                tmpn1 = re.search(r">([^<>]{0,6}[\[〔][0-9]{4}[〕\]][^<>]{0,6}号)", content).group(1)
            except:
                pass
            try:
                tmpn = response.xpath('//div[@class="zw"]/p[2]').xpath('string(.)').extract_first()
            except:
                pass

            if tmpn1:
                if len(tmpn1) < 20:
                    item["legalDocumentNumber"] = tmpn1
            elif tmpn:
                if re.search(r"第[0-9]+?号", tmpn) and len(tmpn) < 20:
                    item["legalDocumentNumber"] = response.xpath('//div[@class="zw"]/p[1]').xpath('string(.)').extract_first() + tmpn
                    item["legalDocumentNumber"] = tools.clean(item["legalDocumentNumber"])
                else:
                    try:
                        tmpn3 = response.xpath('//div[@class="zw"]//p[@style="text-align: center;"]').xpath('string(.)').extract_first()
                        if re.search("[0-9]", tmpn3) and len(tmpn3) < 45:
                            item["legalDocumentNumber"] = tools.clean(tmpn3)
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
