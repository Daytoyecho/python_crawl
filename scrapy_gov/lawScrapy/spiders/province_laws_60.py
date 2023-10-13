# -*- coding:utf-8 -*-
from copy import deepcopy
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
# scrapy crawl province_laws_60


class ProvinceLaw60Spider(scrapy.Spider):
    name = 'province_laws_60'
    allowed_domains = ['shandong.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://www.shandong.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=66&perpage=25&unitid=526463&webid=410&path=http://www.shandong.gov.cn/&webname=%E5%B1%B1%E4%B8%9C%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C&col=1&columnid=107860&sourceContentType=1&permissiontype=0"

        baseform = "col=1&webid=410&path=http%3A%2F%2Fwww.shandong.gov.cn%2F&columnid=107860&sourceContentType=1&unitid=526463&webname=%25E5%25B1%25B1%25E4%25B8%259C%25E7%259C%2581%25E4%25BA%25BA%25E6%25B0%2591%25E6%2594%25BF%25E5%25BA%259C&permissiontype=0"
        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.shandong.gov.cn/col/col107860/index.html?uid=526463&pageNum=2'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        yield scrapy.Request(start_url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('href="([^"]+?)"', response.text)
        law_title_list = re.findall('<a target="_blank" title="([^"]+?)"', response.text)
        law_time_list = re.findall('<span>(.+?)</span>', response.text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "山东省政府-省委有关文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="wip_art_con"]').extract_first()
            fujian = response.xpath('//div[@class="wip_art_con"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="wip_art_con"]//a[@href]').xpath('string(.)').extract()

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
