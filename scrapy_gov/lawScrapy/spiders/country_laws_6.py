# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_6


class CountryLaw6Spider(scrapy.Spider):
    name = 'country_laws_6'
    allowed_domains = ['sousuo.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://sousuo.gov.cn/column/30469/{}.htm'
        start_url = ['http://sousuo.gov.cn/column/30469/0.htm']

        for i in range(1, 77):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//ul[@class="listTxt"]/li/h4/a[1]/@href').extract()
        law_title = response.xpath('//ul[@class="listTxt"]/li/h4/a[1]/text()').extract()
        law_time = response.xpath('//ul[@class="listTxt"]/li/h4/span/text()').extract()

        for i in range(len(law_url_list)):
            # self.count += 1
            # print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl == 'http://www.gov.cn/zhengce/content/2016-02/25/content_5046212.htm':
                print("1212312312312312312312", response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.check_if_all, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def check_if_all(self, response):
        if response.xpath('//div[@id="pageBreak"]/div/a[contains(text(),"全文")]').extract():
            yield scrapy.Request(response.url+"#allContent", self.parse_article, meta={"title": response.meta['title'], "time": response.meta['time']}, dont_filter=False, headers=tools.header)
        else:
            yield scrapy.Request(response.url, self.parse_article, meta={"title": response.meta['title'], "time": response.meta['time']}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国务院"
        item["legalCategory"] = "国务院政策"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y.%m.%d"))

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            legalDocumentNumber = response.xpath('//div[@class="wrap"]/table[1]//table[1]//tr[4]/td[2]/text()').extract_first()
            if legalDocumentNumber:
                if re.search(r'[0-9]', legalDocumentNumber):
                    item["legalDocumentNumber"] = legalDocumentNumber

            content = response.xpath('//*[@id="UCAP-CONTENT"]').extract_first()
            fujian = response.xpath('//*[@id="UCAP-CONTENT"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="UCAP-CONTENT"]//a[@href]').xpath('string(.)').extract()

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
