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
# scrapy crawl province_laws_126


class ProvinceLaw126Spider(scrapy.Spider):
    name = 'province_laws_126'
    allowed_domains = ['zwgk.hlj.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = 'https://zwgk.hlj.gov.cn/zwgk/publicInfo/searchFile?chanPath=2,212,'

        baseform = "page=1&limit=96&total=96"

        header = deepcopy(tools.header)
        header['Referer'] = 'https://zwgk.hlj.gov.cn/zwgk/gzk_index'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        yield scrapy.Request(start_url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)['data']['records']
        baseu = "https://zwgk.hlj.gov.cn/zwgk/gzk/detail?id={}"
        for item in data:

            tmpurl = baseu.format(str(item['id']))
            law_title = item['title']
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(item['publishTime'])))
            law_text = item['gzInfo']

            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "text": law_text}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "黑龙江省"
        item["legalCategory"] = "黑龙江省政府-规章库"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        wenhao = re.search("日(.+?号)", response.meta["text"]).group(1)
        item["legalDocumentNumber"] = tools.clean(wenhao)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

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
