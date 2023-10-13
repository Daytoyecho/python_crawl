# -*- coding:utf-8 -*-
import scrapy
import datetime
from lawScrapy.items import LawscrapyItem
import re
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

# scrapy crawl province_laws_26


class ProvinceLaw26Spider(scrapy.Spider):
    name = 'province_laws_26'
    allowed_domains = ['sz.gov.cn']

    url_list = []
    count = 0

    def start_requests(self):

        start_url = ['http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/zcfg/index.html',
                     'http://zxqyj.sz.gov.cn/zwgk/zfxxgkml/zcfg/index_2.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        data_list = response.xpath('//div[@class="nei_listCont AllFont"]//li')

        for item in data_list:

            tmpurl = item.xpath('./a/@href').extract_first()
            law_title = item.xpath('./a/text()').extract_first()
            law_time = item.xpath('./span/text()').extract_first()

            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            0/0
        item["legalProvince"] = "广东省"
        item["legalCategory"] = "深圳市政府-政策法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="TRS_Editor"]').extract_first()
            fujian = response.xpath('//div[contains(@class,"xxTextCont")]//a/@href').extract()
            fujian_name = response.xpath('//div[contains(@class,"xxTextCont")]//a[@href]').xpath('string(.)').extract()

            try:
                tmp = re.search(r'>([^<>]*?[\[〔][0-9]{4}[〕\]][^<>]*?)<', content).group(1)
                if len(tmp) < 20:
                    item["legalDocumentNumber"] = tmp
                if re.search('〔', content) and not item["legalDocumentNumber"]:
                    item["legalDocumentNumber"] = "人工审查"
            except:
                pass

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
