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
# scrapy crawl province_laws_71


class ProvinceLaw71Spider(scrapy.Spider):
    name = 'province_laws_71'
    allowed_domains = ['chengdu.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://api.rcmail.cn/govInfoPub/infoList.action?x-msc-token=xEFvsIO1mO3DXOtZsqLLSGIAcwn4Ug9t&classId=07030202090101&sw=&cy=&fn=&sd=&ed=&pageNum={}&pageSize=14&result=json&tdsourcetag=s_pcqq_aiomsg"

        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.chengdu.gov.cn/'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 8):
            time.sleep(0.2)
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary,  dont_filter=True, headers=header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)['datalist']
        for item in data:
            id = item['id']
            index = item['index']
            tmpurl = "http://api.rcmail.cn/govInfoPub/detail.action?id={}&tn=6&result=json&x-msc-token=xEFvsIO1mO3DXOtZsqLLSGIAcwn4Ug9t".format(id)
            law_title = item["name"]
            law_time = item["time"]
            law_number = item["filenumber"]

            if tmpurl not in self.url_list:
                time.sleep(0.2)
                self.count += 1
                print(self.count)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"id": id, "index": index, "title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = "http://www.chengdu.gov.cn/chengdu/c131029/zcwjney.shtml?id={}&tn=6&wz=%E6%94%BF%E5%BA%9C%E4%BB%A4&index={}".format(str(response.meta['id']), response.meta['index'])
        item["legalProvince"] = "四川省"
        item["legalCategory"] = "成都市政府-政府文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        wenhao = tools.clean(response.meta["number"])
        if wenhao:
            item["legalDocumentNumber"] = wenhao

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        data = json.loads(response.text)
        content = data['datacontent']['content']

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
