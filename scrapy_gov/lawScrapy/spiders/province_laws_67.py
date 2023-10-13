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
# scrapy crawl province_laws_67


class ProvinceLaw67Spider(scrapy.Spider):
    name = 'province_laws_67'
    allowed_domains = ['shandong.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        with open("lawScrapy/spiders/p67.json", 'r', encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            tmpurl = item["url"]
            law_title = item["title"]
            law_time = item["time"][:10]
            law_number = item["fileno"]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "福建省"
        item["legalCategory"] = "福建省政府-法律法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            fujian = response.xpath('//div[@class="TRS_Editor"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract()

            if not content:
                content = response.xpath('//div[contains(@id,"detailCont")]').extract_first()
                fujian = response.xpath('//div[contains(@id,"detailCont")]//a/@href').extract()
                fujian_name = response.xpath('//div[contains(@id,"detailCont")]//a[@href]').xpath('string(.)').extract()
            wenhao = tools.clean(response.meta["number"])
            if wenhao:
                item["legalDocumentNumber"] = wenhao
            else:
                wenhao = response.xpath('//div[@class="TRS_Editor"]/p[2]').xpath('string(.)').extract_first()
                if wenhao and re.search('〔.+〕第.+号', tools.clean(wenhao)):
                    item["legalDocumentNumber"] = tools.clean(response.xpath('//div[@class="TRS_Editor"]/p[1]').xpath('string(.)').extract_first() + wenhao)

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
