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

# scrapy crawl province_laws_152


class ProvinceLaw152Spider(scrapy.Spider):
    name = 'province_laws_152'
    allowed_domains = ['nmg.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = ['http://jrj.nmg.gov.cn/zcfg/zcwj/index.html', 'http://jrj.nmg.gov.cn/zcfg/zcwj/index_1.html']

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//div[@class="n_txt"]//li/i/a/@href').extract()
        law_title = response.xpath('//div[@class="n_txt"]//li/i/a/text()').extract()
        law_time = response.xpath('//div[@class="n_txt"]//li/span/text()').extract()

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
        item["legalProvince"] = "内蒙古自治区"
        item["legalCategory"] = "内蒙古自治区金融工作办公室-政策法规自治区政策"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(response.meta['time'], "%Y-%m-%d %H:%M:%S"))

        # 这个文号处理太麻烦，一共22个你复制一下填到数据库里(*^_^*)
        item["legalDocumentNumber"] = ""

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="pagecontent"]').extract_first()
            fujian = response.xpath('//*[@id="pagecontent"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="pagecontent"]//a[@href]').xpath('string(.)').extract()
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
