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
# scrapy crawl province_laws_53


class ProvinceLaw53Spider(scrapy.Spider):
    name = 'province_laws_53'
    allowed_domains = ['jiangsu.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = ["http://jsgzw.jiangsu.gov.cn/module/xxgk/search.jsp?texttype=&fbtime=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage=1&sortfield=&fields=&fieldConfigId=&hasNoPages=&infoCount=",
                     "http://jsgzw.jiangsu.gov.cn/module/xxgk/search.jsp?texttype=&fbtime=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage=2&sortfield=&fields=&fieldConfigId=&hasNoPages=&infoCount="]

        baseform = 'infotypeId=10&jdid=39&area=&divid=div125&vc_title=&vc_number=&currpage={}&vc_filenumber=&vc_all=&texttype=&fbtime=&texttype=&fbtime=&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=&fields=&fieldConfigId=&hasNoPages=&infoCount='
        header = deepcopy(tools.header)
        header['Referer'] = 'http://jsgzw.jiangsu.gov.cn/col/col49542/index.html?number=10'
        header['Content-Type'] = 'application/x-www-form-urlencoded'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`;')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(len(start_url)):
            yield scrapy.Request(start_url[i], body=baseform.format(str(i+1), str(i+1)), method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        data_list = response.xpath('//*[@class="xlt_table0"]/tr[position()>1]')
        for item in data_list:
            tmpurl = item.xpath('./td[2]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)

            law_title = item.xpath('./td[2]/a/@title').extract_first()
            law_time = item.xpath('./td[4]/text()').extract_first()
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1.5)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江苏省"
        item["legalCategory"] = "江苏省人民政府国有资产监督管理委员会-政策解读"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = re.search(r'<meta name="ContentStart">([\s\S]+?)<meta name="ContentEnd">', response.text).group(1)
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            tmpn = response.xpath('//*[@class="xlt_table"]//tr[2]/td[4]/text()').extract_first()
            if tmpn and re.search(r'\d', tmpn):
                item["legalDocumentNumber"] = tools.clean(tmpn)

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
