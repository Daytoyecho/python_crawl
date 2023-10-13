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
# scrapy crawl province_laws_55


class ProvinceLaw55Spider(scrapy.Spider):
    name = 'province_laws_55'
    allowed_domains = ['nanjing.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url1 = "https://www.nanjing.gov.cn/igs/front/search/publish/data/list.html?&index=wzqsearch-v20190124&type=infomation&siteId=3&pageSize=20&orderProperty=DOCRELTIME&pageIndex={}&orderDirection=desc&filter%5BSITEID%5D=3&filter%5BCHANNELID%5D=21985&filter%5BGROUPCAT%5D=394%2C397%2C2604%2C396&pageNumber=1"
        start_url2 = "https://www.nanjing.gov.cn/igs/front/search/publish/data/list.html?&index=wzqsearch-v20190124&type=infomation&siteId=3&pageSize=20&orderProperty=DOCRELTIME&pageIndex=3&orderDirection=desc&filter%5BSITEID%5D=3&filter%5BCHANNELID%5D=21985&filter%5BGROUPCAT%5D=394%2C397%2C2604%2C396&pageNumber={}"

        header = deepcopy(tools.header)
        header['Referer'] = 'https://www.nanjing.gov.cn/zdgk/214/394/index_17989_1.html'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 4):
            yield scrapy.Request(start_url1.format(i), self.parse_dictionary, dont_filter=False, headers=header)
        for i in range(4, 17):
            yield scrapy.Request(start_url2.format(i), self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data = json.loads(response.text)

        for item in data['rows']:
            tmpurl = tools.clean(item['DOCPUBURL'])
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(item['DOCTITLE'])
            law_time = tools.clean(item['DOCRELTIME'][:19])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1.5)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江苏省"
        item["legalCategory"] = "南京市政府-法规规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        tim = time.mktime(time.strptime(response.meta['time'], "%Y-%m-%dT%H:%M:%S"))
        item["legalPublishedTime"] = tools.UTCTsToLocalDt(tim)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[contains(@class,"TRS_UEDITOR")]').extract_first()
            fujian = response.xpath('//*[@class="t1"]//a/@href').extract()
            fujian_name = response.xpath('//*[@class="t1"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@class="wenZhang"]').extract_first()
                content = re.sub(r'<div class="con_f">[\s\S]+?</div>', '', content)
            tmpn = response.xpath('//*[@class="t1"]//tr[5]/td[2]/text()').extract_first()
            if tmpn and re.search(r'\d', tmpn):
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
