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
# scrapy crawl province_laws_54


class ProvinceLaw54Spider(scrapy.Spider):
    name = 'province_laws_54'
    allowed_domains = ['jiangsu.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://jsgzw.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=58&perpage=20"

        baseform = 'col=1&appid=1&webid=39&path=%2F&columnid=61490&sourceContentType=1&unitid=247686&webname=%E6%B1%9F%E8%8B%8F%E7%9C%81%E5%9B%BD%E8%B5%84%E5%A7%94&permissiontype=0'
        header = deepcopy(tools.header)
        header['Referer'] = 'http://jsgzw.jiangsu.gov.cn/col/col61490/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        yield scrapy.Request(start_url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('<a href="([^"]+?)"', response.text)
        law_title_list = re.findall('target="_blank">([^"]+?)<', response.text)
        law_time_list = re.findall('<span class="fr">([^<>]+?)</span>', response.text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1.5)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江苏省"
        item["legalCategory"] = "江苏省人民政府国有资产监督管理委员会-政策文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = re.search(r'<meta name="ContentStart">([\s\S]+?)<meta name="ContentEnd">', response.text).group(1)
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            tmpn = re.search(r'>([\s\S]+?[0-9]+号)', content)
            if tmpn and len(tmpn.group(1)) < 20:
                item["legalDocumentNumber"] = tools.clean(tmpn.group(1))

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
