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
# scrapy crawl province_laws_80


class ProvinceLaw80Spider(scrapy.Spider):
    name = 'province_laws_80'
    allowed_domains = ['wuhan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://www.wuhan.gov.cn/zwgk/xxgk/zfgz_new/"

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        yield scrapy.Request(start_url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        text = response.text
        url_list = re.findall(r"var dUrl = '([^']+?)'", text)
        title_list = re.findall(r"var dTitle = '([^']+?)'", text)
        text_list = re.findall(r"var dRN = '([^']+?)'", text)
        number_list = re.findall(r"var dFN = '([^']+?)'", text)
        content_list = re.findall(r"var dCon = '([\s\S]+?)'[\n ]+var dText ='';", text)

        for i in range(len(url_list)):
            tmpurl = url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = title_list[i]
            law_time = re.search(r'[（(]?([^日]+?日)', text_list[i]).group(1)
            law_content = content_list[i]
            law_number = number_list[i]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.3)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "content": law_content, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "湖北省"
        item["legalCategory"] = "武汉市政府-政府规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'], "%Y年%m月%d日"))
        if response.meta['number']:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.meta['content'].replace("\/", "/")

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
