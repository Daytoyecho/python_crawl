# -*- coding:utf-8 -*-
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
# scrapy crawl province_laws_73


class ProvinceLaw73Spider(scrapy.Spider):
    name = 'province_laws_73'
    allowed_domains = ['hunan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "http://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/wjk_glrb_{}.html"
        start_url = ['http://www.hunan.gov.cn/hnszf/xxgk/wjk/szfbgt/wjk_glrb.html']
        for i in range(2, 35):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//table[@class="table"]/tbody/tr')
        for item in data_list:

            tmpurl = item.xpath('./td[@class="txt-left"]/a/@href').extract_first()
            law_title = item.xpath('./td[@class="txt-left"]/a/text()').extract_first()
            law_time = item.xpath('./td[4]/text()').extract_first()
            law_number = item.xpath('./td[3]/script/text()').extract_first()
            try:
                law_number = re.search(r"var fileNum='([^']+?)'", law_number).group(1)
            except:
                law_number = ""
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "湖南省"
        item["legalCategory"] = "湖南省政府-省政府办公厅文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if response.meta["number"]:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="zoom"]').extract_first()
            text = response.xpath('//div[@class="xly_Box"]/script/text()').extract_first()
            fujian = re.findall(r"path\.push\('([^']+?)'", text)
            fujian_name = re.findall(r"memo\.push\('([^']+?)'", text)

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
