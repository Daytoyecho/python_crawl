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

# scrapy crawl province_laws_149


class ProvinceLaw149Spider(scrapy.Spider):
    name = 'province_laws_149'
    allowed_domains = ['nmg.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "https://www.nmg.gov.cn/zwgk/gzk/index_{}.html"
        start_url = ['https://www.nmg.gov.cn/zwgk/gzk/index.html']

        for i in range(1, 6):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="title l"]/p/a/@href').extract()
        law_title = response.xpath('//div[@class="title l"]/p/a/text()').extract()
        tmp_text = response.xpath('//div[@class="title l"]/i/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "text": tmp_text[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "内蒙古自治区"
        item["legalCategory"] = "内蒙古自治区政府-规章库"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        if re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']):
            tmp_time = re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']).group(1)
            item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time.strip(), "%Y年%m月%d日"))
        else:
            item["legalPublishedTime"] = ""

        if re.search(r'(内蒙古自治区人民政府令第[0-9]{0,4}号)', response.meta['text']):
            item["legalDocumentNumber"] = re.search(r'(内蒙古自治区人民政府令第[0-9]{0,4}号)', response.meta['text']).group(1)
        else:
            item["legalDocumentNumber"] = ""

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="text"]').extract_first()
            fujian = response.xpath('//div[@class="text"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="text"]//a[@href]').xpath('string(.)').extract()

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
