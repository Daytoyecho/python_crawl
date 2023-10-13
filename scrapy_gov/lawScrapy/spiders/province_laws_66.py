# -*- coding:utf-8 -*-
from copy import deepcopy
from email import header
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
import base64
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl province_laws_66


class ProvinceLaw66Spider(scrapy.Spider):
    name = 'province_laws_66'
    allowed_domains = ['jinan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        infotypeId = ['A060414', 'A060402', 'A060413', 'A060401', 'A060415', 'A060446']

        start_url1 = "http://www.jinan.gov.cn/module/xxgk/mobile_search.jsp?standardXxgk=1&isAllList=1&texttype=&fbtime=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=compaltedate:0&fields=&fieldConfigId=&hasNoPages=&infoCount="
        baseform1 = "infotypeId={}&jdid=1&area=&divid=div55372&vc_title=&vc_number=&sortfield=compaltedate:0&currpage={}&vc_filenumber=&vc_all=&texttype=&fbtime=&standardXxgk=1&isAllList=1&texttype=&fbtime=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=compaltedate:0&fields=&fieldConfigId=&hasNoPages=&infoCount="

        header = deepcopy(tools.header)
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        id = '50'
        for i in range(6):
            yield scrapy.Request(start_url1.format(id), body=baseform1.format(infotypeId[i], id, id), method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        url_list = response.xpath('//*[@class="zfxxgk_zdgkc"]//li/a/@href').extract()
        title_list = response.xpath('//*[@class="zfxxgk_zdgkc"]//li/a/@title').extract()
        time_list = response.xpath('//*[@class="zfxxgk_zdgkc"]//li/b/text()').extract()

        header = deepcopy(tools.header)
        header['Cache-Control'] = "max-age=0"
        header['Upgrade-Insecure-Requests'] = 1

        for i in range(len(url_list)):
            tmpurl = url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = title_list[i]
            law_time = time_list[i]

            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "济南市政府-其他文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="zoom"]').extract_first()
            fujian = response.xpath('//div[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//div[@class="wz"]/table//tr[3]/td[2]/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = tools.clean(wenhao)

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
