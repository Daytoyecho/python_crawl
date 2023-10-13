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
# scrapy crawl province_laws_84


class ProvinceLaw84Spider(scrapy.Spider):
    name = 'province_laws_84'
    allowed_domains = ['wuhan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        base = "http://www.wuhan.gov.cn/zwgk/xxgk/zcjd/index_{}.shtml"
        start_url = ["http://www.wuhan.gov.cn/zwgk/xxgk/zfwj/zcjd/index.shtml"]

        for i in range(71):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        url_list = response.xpath('//div[@class="articleList"]//li/a/@href').extract()
        title_list = response.xpath('//div[@class="articleList"]//li/a/text()').extract()
        time_list = []
        for i in response.xpath('//div[@class="articleList"]//li/span'):
            time_list.append("".join(i.xpath('./text()').extract()))

        for i in range(len(url_list)):
            tmpurl = url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = title_list[i]
            law_time = time_list[i]
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "湖北省"
        item["legalCategory"] = "武汉市政府-政策解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'].strip(), "%Y年%m月%d日"))

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[contains(@class,"TRS_UEDITOR")]').extract_first()
            fujian = response.xpath('//*[@id="articleFJ"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="articleFJ"]//a[@href]').xpath('string(.)').extract()
            if not content:
                content = response.xpath('//*[@class="TRS_Editor"]').extract_first()
                fujian.extend(response.xpath('//*[@class="TRS_Editor"]//a/@href').extract())
                fujian_name.extend(response.xpath('//*[@class="TRS_Editor"]//a[@href]').xpath('string(.)').extract())
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
