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
# scrapy crawl country_laws_1


class CountryLaw1Spider(scrapy.Spider):
    name = 'country_laws_1'
    allowed_domains = ['npc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = 'http://www.npc.gov.cn/npc/c12488/list_{}.shtml'
        start_url = ['http://www.npc.gov.cn/npc/c12488/list.shtml']
        for i in range(2, 35):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com("SELECT legalUrl FROM `law`")
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="fl s_lw"]//li/a/@href').extract()
        law_title = response.xpath('//div[@class="fl s_lw"]//li/a/text()').extract()
        law_time = response.xpath('//div[@class="fl s_lw"]//li/span/text()').extract()

        for i in range(len(law_url_list)):
            self.count += 1
            print(self.count)
            tmpurl = tools.getpath(law_url_list[i], response.url)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title[i], "time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "全国人民代表大会"
        item["legalCategory"] = "全国人大-权威发布法律文件"

        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        if re.search(r'（(第[^）]+号)）', item["legalPolicyName"]):
            item["legalDocumentNumber"] = item["legalPolicyName"]

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@id="Zoom"]').extract_first()
            fujian = response.xpath('//div[@id="Zoom"]//a/@href').extract()
            fujian_name = response.xpath('//div[@id="Zoom"]//a[@href]').xpath('string(.)').extract()
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
