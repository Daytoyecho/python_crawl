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
# scrapy crawl province_laws_39


class ProvinceLaw39Spider(scrapy.Spider):
    name = 'province_laws_39'
    allowed_domains = ['gz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://www.zj.gov.cn/module/xxgk/search.jsp?standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=,compaltedate:0"

        baseform = "infotypeId=C0202&jdid=3096&area=&divid=div1229498488&vc_title=&vc_number=&sortfield=,compaltedate:0&currpage={}&vc_filenumber=&vc_all=&texttype=1&fbtime=-1&standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=,compaltedate:0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.zj.gov.cn'
        header['Referer'] = 'http://www.zj.gov.cn/col/col1545743/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        header['Cookie'] = "zh_choose_undefined=s; cssstyle=1; ZJYHZXSESSIONID=868061f1-6672-4277-b20c-df52b63f1ed5; SERVERID=b2ba659a0bf802d127f2ffc5234eeeba|1652799516|1652793586"
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 102):
            data = baseform.format(str(i), str(i))
            yield scrapy.Request(start_url.format(str(i)), body=data, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        dta_list = response.xpath('//*[@class="zcwj-con-right_list"]/div')
        for item in dta_list:
            tmpurl = item.xpath('./span[1]/a/@href').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(item.xpath('./span[1]/a/text()').extract_first())
            law_time = tools.clean(item.xpath('./span[contains(@class,"cont_right_from4")]/text()').extract_first())
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "浙江省"
        item["legalCategory"] = "浙江省政府-其他文件-省政府办公厅"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            item["legalDocumentNumber"] = tools.clean(response.xpath('//*[@class="xxgk-info-wh"]/td/text()').extract_first())

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
