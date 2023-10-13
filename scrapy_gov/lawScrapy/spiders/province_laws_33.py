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
# scrapy crawl province_laws_33


class ProvinceLaw33Spider(scrapy.Spider):
    name = 'province_laws_33'
    allowed_domains = ['gz.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = "http://www.zj.gov.cn/module/xxgk/search.jsp?standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=,createdatetime:0,orderid:0"

        baseform = "infotypeId=A0212&jdid=3096&area=&divid=div1229498488&vc_title=&vc_number=&sortfield=,createdatetime:0,orderid:0&currpage={}&vc_filenumber=&vc_all=&texttype=1&fbtime=-1&standardXxgk=0&isAllList=1&texttype=1&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage={}&sortfield=,createdatetime:0,orderid:0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.zj.gov.cn'
        header['Referer'] = 'http://www.zj.gov.cn/col/col1229005922/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        header['Cookie'] = "zh_choose_undefined=s; ZJYHZXSESSIONID=7fd52b24-89aa-49d2-bf92-3e7309581f11; cssstyle=1; SERVERID=a6d2b4ba439275d89aa9b072a5b72803|1652777188|1652776481"
        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 32):
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
        item["legalCategory"] = "浙江省政府-地方性法规"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            for i in response.xpath('//*[@id="zoom"]//p').xpath('string(.)').extract():
                if not i:
                    continue
                if len(tools.clean(i)) < 30:
                    tmpn = re.search(r"([\S]{0,25}第[0-9]+号)", tools.clean(i))
                    if tmpn:
                        if len(tmpn.group(1)) < 6:
                            item["legalDocumentNumber"] = tools.clean(response.xpath('//*[@id="zoom"]//p[1]').xpath('string(.)').extract_first() + tmpn.group(1))
                        else:
                            item["legalDocumentNumber"] = tmpn.group(1)

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
