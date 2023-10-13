# -*- coding:utf-8 -*-
from copy import deepcopy
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
# scrapy crawl province_laws_65


class ProvinceLaw65Spider(scrapy.Spider):
    name = 'province_laws_65'
    allowed_domains = ['jinan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://www.jinan.gov.cn/module/xxgk/search_custom.jsp?fields=&fieldConfigId=94973&sortfield=compaltedate:0,createdatetime:0&fbtime=&texttype=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&binlay=&c_issuetime="

        baseform = "infotypeId=%2C246%2C253%2C626%2C627%2C628%2C10951%2C14799%2C&jdid=1&area=1137010000418859XL&fields=&fieldConfigId=94973&hasNoPages=0&infoCount=14&sortfield=compaltedate%3A0%2Ccreatedatetime%3A0"
        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.jinan.gov.cn/module/xxgk/search_custom.jsp?infotypeId=246,253,626,627,628,10951,14799&fieldConfigId=94973&area=1137010000418859XL'
        header['Content-Type'] = 'application/x-www-form-urlencoded'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 18):
            yield scrapy.Request(start_url.format(str(i)), body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//*[@class="searchborder1"]//tr[position()>1]')

        for item in data_list:
            tmpurl = item.xpath('./td[1]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = item.xpath('./td[1]/a/text()').extract_first()
            law_time = item.xpath('./td[5]/text()').extract_first()
            law_number = item.xpath('./td[2]/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "济南市政府-规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if response.meta['number']:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="zoom"]').extract_first()
            fujian = response.xpath('//div[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="zoom"]//a[@href]').xpath('string(.)').extract()

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
