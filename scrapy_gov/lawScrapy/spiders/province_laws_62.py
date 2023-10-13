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
# scrapy crawl province_laws_62


class ProvinceLaw62Spider(scrapy.Spider):
    name = 'province_laws_62'
    allowed_domains = ['shandong.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        with open("lawScrapy/spiders/p62.txt", 'r', encoding="utf-8") as f:
            text = f.read()

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        law_url_list = re.findall('href="([^"]+?)"', text)
        law_title_list = re.findall('<a target="_blank" title="([^"]+?)"', text)
        law_time_list = re.findall('<span>(.+?)</span>', text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, "http://www.shandong.gov.cn/col/col97741/index.html")
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "山东省政府-规范性文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="wip_art_con"]').extract_first()
            fujian = response.xpath('//div[@class="wip_art_con"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="wip_art_con"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//div[@class="people-desc"]//tr/td/strong[contains(text(),"发文字号")]/../text()').extract_first()
            if wenhao and re.search(r'号', wenhao) and len(tools.clean(wenhao)) < 25:
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
