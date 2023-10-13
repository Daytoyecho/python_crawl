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
# scrapy crawl province_laws_69


class ProvinceLaw69Spider(scrapy.Spider):
    name = 'province_laws_69'
    allowed_domains = ['chengdu.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://gk.chengdu.gov.cn/govInfo/list-fggw.action?classId=07030202090101&sw=&fn=&page={}&size=15"

        header = deepcopy(tools.header)
        header['Referer'] = 'http://gk.chengdu.gov.cn/govInfo/rules.html'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 7):
            time.sleep(5)
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary,  dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)['data']['data']
        for item in data:
            id = str(item["id"])
            tmpurl = "http://gk.chengdu.gov.cn/govInfo/detail-fggw.action?id={}".format(id)

            law_title = item["title"]
            law_time = item["issueDate"][:10]
            law_number = item["fileNumber"]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"id": id, "title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = "http://gk.chengdu.gov.cn/govInfo/detail-fggw.html?id={}&tn=6".format(response.meta['id'])
        item["legalProvince"] = "四川省"
        item["legalCategory"] = "成都市政府-规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        wenhao = tools.clean(response.meta["number"])
        if wenhao:
            item["legalDocumentNumber"] = wenhao

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        data = json.loads(response.text)
        content = data['data']['content']

        item['legalContent'] = content
        tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.url)

        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.url)
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
