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
# scrapy crawl country_laws_4


class CountryLaw4Spider(scrapy.Spider):
    name = 'country_laws_4'
    allowed_domains = ['saac.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = ['https://www.saac.gov.cn/daj/gfxwj/dazc_list.shtml', "https://www.saac.gov.cn/daj/gfxwj/dazc_list_2.shtml", "https://www.saac.gov.cn/daj/gfxwj/dazc_list_3.shtml"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="listright"]/ul[2]/li/a/@href').extract()
        law_title = response.xpath('//div[@class="listright"]/ul[2]/li/a/@title').extract()

        for i in range(len(law_url_list)):
            self.count += 1
            print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国国家档案局"
        item["legalCategory"] = "国家档案局-规范性文件"
        item["legalPolicyName"] = tools.clean(re.search(r"[0-9]+\.(.+)", response.meta['title']).group(1))

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            item["legalPublishedTime"] = response.xpath('//div[@class="pages-date"]/span[1]/text()').extract_first()
            item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(item["legalPublishedTime"].strip(), "%Y年%m月%d日"))

            content = response.xpath('//div[@class="pages_content"]').extract_first()
            fujian = response.xpath('//div[@class="pages_content"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="pages_content"]//a[@href]').xpath('string(.)').extract()

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
