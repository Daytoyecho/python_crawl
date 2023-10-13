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
# scrapy crawl province_laws_127


class ProvinceLaw127Spider(scrapy.Spider):
    name = 'province_laws_127'
    allowed_domains = ['zwgk.hlj.gov.cn']
    url_list = []
    wrong = 0
    count = 0

    def start_requests(self):

        start_url = 'https://zwgk.hlj.gov.cn/zwgk/publicInfo/searchFile?chanPath=2,213,'

        baseform = "chanId=213&chanP=2%2C213%2C&chanName=%E8%A1%8C%E6%94%BF%E8%A7%84%E8%8C%83%E6%80%A7%E6%96%87%E4%BB%B6&page={}&limit=100&total=369"

        header = deepcopy(tools.header)
        header['Referer'] = 'https://zwgk.hlj.gov.cn/zwgk/zc_list?chanId=213&chanP=2,213,&chanName=%E8%A1%8C%E6%94%BF%E8%A7%84%E8%8C%83%E6%80%A7%E6%96%87%E4%BB%B6'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 5):
            yield scrapy.Request(start_url, body=baseform.format(str(i)), method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)['data']['records']
        baseu = "https://zwgk.hlj.gov.cn/zwgk/publicInfo/detail?id={}"
        for item in data:

            tmpurl = baseu.format(str(item['id']))
            law_title = item['title']
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(item['publishTime'])))
            law_number = item["fileNumber"]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "黑龙江省"
        item["legalCategory"] = "黑龙江省政府-行政规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@class="zwnr"]').extract_first()
            fujian = response.xpath('//*[@class="zwnr"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="zwnr"]//a[@href]').xpath('string(.)').extract()

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
