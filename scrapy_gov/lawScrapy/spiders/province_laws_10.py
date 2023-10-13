# -*- coding:utf-8 -*-
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
import pdfkit
import json
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

# scrapy crawl province_laws_10


class ProvinceLaw120Spider(scrapy.Spider):
    name = 'province_laws_10'
    allowed_domains = ['shanghai.gov.cn']
#-------------------------------------------------------------#
    url_list = []
    count = 0

    def start_requests(self):

        base = 'https://www.shanghai.gov.cn/xxzfgzwj/index_{}.html'
        start_url = ['https://www.shanghai.gov.cn/xxzfgzwj/index.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law` where legalUrl LIKE "https://www.shanghai.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(2, 31):
            start_url.append(base.format(str(i)))

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//table[@class="r-table"]/tbody//tr//td[2]//a/@href').extract()
        law_title = response.xpath('//table[@class="r-table"]/tbody//tr//td[2]//a/p[1]/text()').extract()
        law_time = response.xpath('//table[@class="r-table"]/tbody//tr//td[2]//a/p[2]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "上海市"
        item["legalCategory"] = "上海市政府-政府规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        tmp_text = response.meta['time']
        if re.search(r'[（\(][0-9]+年[0-9]+月[0-9]+日', tmp_text):
            tmp_time = re.search(r'[（\(]([0-9]+年[0-9]+月[0-9]+日)', tmp_text).group(1)
            item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time, "%Y年%m月%d日"))

        if re.search(r'(上海市人民政府令第[0-9]{0,4}号)', tmp_text):
            item["legalDocumentNumber"] = re.search(r'日([\s\S]+?[0-9]{0,4}号)', tmp_text).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="Article_content"]').extract_first()
            fujian = response.xpath('//div[@class="Article_content"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="Article_content"]//a[@href]').xpath('string(.)').extract()

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
