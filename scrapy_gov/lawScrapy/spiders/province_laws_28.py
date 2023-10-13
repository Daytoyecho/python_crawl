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
# scrapy crawl province_laws_28


class ProvinceLaw28Spider(scrapy.Spider):
    name = 'province_laws_28'
    allowed_domains = ['sz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://jr.sz.gov.cn/gkmlpt/api/all/2811?page={}&sid=755031'
        start_url = []
        for i in range(1, 3):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['articles']

        for item in data_list:

            tmpurl = item['url']
            law_title = item['title']
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(item["first_publish_time"])))
            law_number = item['document_number']
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, "number": law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "广东省"
        item["legalCategory"] = "深圳市地方金融监督管理局-政策法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if response.meta['number']:
            item["legalDocumentNumber"] = tools.clean(response.meta['number'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            fujian = response.xpath('//div[@class="article-content"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="article-content"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//div[@class="article-content"]').extract_first()
            if not content:
                content = response.xpath('//div[@class="zw"]').extract_first()
                fujian = response.xpath('//div[@class="zw"]//a/@href').extract()
                fujian_name = response.xpath('//div[@class="zw"]//a[@href]').xpath('string(.)').extract()
            content = re.sub(r'style="width: 700px"', "", content, flags=re.I)

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
