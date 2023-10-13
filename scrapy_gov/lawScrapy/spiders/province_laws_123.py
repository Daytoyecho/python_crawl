# -*- coding:utf-8 -*-
import requests
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)


class ProvinceLaw123Spider(scrapy.Spider):
    name = 'province_laws_123'
    allowed_domains = ['zwgk.changchun.gov.cn/']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://111.26.164.51:8081/govsearch/jsonp/gkml/zf_jd_list.jsp?page={}&lb=44452&callback=result&sword=&searchColumn=all&searchYear=all&pubURL=http://zwgk.changchun.gov.cn&SType=1&searchColumnYear=all&searchYear=all&pubURL=&SType=1&channelId=44452&_=1653382657539"
        start_url = []
        for i in range(1, 104):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        str = response.text[65:-4]
        str = json.loads(str)
        for i in str['data']:
            tmpurl = i['puburl']
            law_title = i['title']
            law_time = i['tip']['dates']
            law_number = i['tip']['filenum']
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "number": law_number, "times": law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "吉林省"
        item["legalCategory"] = "长春市政府-政府信息公开"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])
        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        item["legalPublishedTime"] = response.meta["times"]
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            print('\n')
            print(response.url)
            content = response.xpath('//div[@class="Custom_UnionStyle"]').extract_first()
            fujian = response.xpath('//div[@class="Custom_UnionStyle"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="Custom_UnionStyle"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[@class="contents_div"]').extract_first()
                fujian = response.xpath('//div[@class="contents_div"]//a/@href').extract()
                fujian_name = response.xpath('//div[@class="contents_div"]//a[@href]').xpath('string(.)').extract()
            # ########如果时间或者文号需要用到xpath或者re，请放到这儿来#########

            # -------------------------------------------------------------#

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
