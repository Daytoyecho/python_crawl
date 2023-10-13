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
# scrapy crawl province_laws_119


class ProvinceLaw119Spider(scrapy.Spider):
    name = 'province_laws_119'
    allowed_domains = ['jiangxi.gov.cn']

    url_list = []
    count = 0

    def start_requests(self):

        start_url = ["http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=100&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=101&endrecord=200&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=201&endrecord=300&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=301&endrecord=400&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=401&endrecord=500&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=501&endrecord=600&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=601&endrecord=700&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=701&endrecord=800&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=801&endrecord=900&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=901&endrecord=1000&perpage=34",
                     "http://jxf.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1001&endrecord=1068&perpage=34"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        baseform = "col=1&webid=230&path=http%3A%2F%2Fjxf.jiangxi.gov.cn%2F&columnid=39218&sourceContentType=1&unitid=375746&webname=%E6%B1%9F%E8%A5%BF%E7%9C%81%E8%B4%A2%E6%94%BF%E5%8E%85&permissiontype=0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://jxf.jiangxi.gov.cn'
        header['Referer'] = 'http://jxf.jiangxi.gov.cn/col/col39218/index.html?uid=375746&pageNum=1'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        for url in start_url:
            yield scrapy.Request(url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall("href='([^']+?)'", response.text)
        law_title_list = re.findall("title='([^']+?)'", response.text)
        law_time_list = re.findall('<span class="bt-data-time">(.*?)</span>', response.text)

        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])

            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.5)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江西省"
        item["legalCategory"] = "江西省财政厅-政策文件"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']
        if re.search(r'(赣.*?[0-9]{0,4}.*?号)', response.meta['title']):
            item["legalDocumentNumber"] = re.search(r'(赣.*?[0-9]{0,4}.*?号)', response.meta['title']).group(1)
        else:
            item["legalDocumentNumber"] = ""

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

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
