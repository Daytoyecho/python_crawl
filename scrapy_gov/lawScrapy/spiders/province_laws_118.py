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
# scrapy crawl province_laws_118


class ProvinceLaw118Spider(scrapy.Spider):
    name = 'province_laws_118'
    allowed_domains = ['jiangxi.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = ["http://www.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=300&perpage=300",
                     "http://www.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=301&endrecord=600&perpage=300",
                     "http://www.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=601&endrecord=617&perpage=17"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        baseform = "col=1&webid=3&path=http%3A%2F%2Fwww.jiangxi.gov.cn%2F&columnid=48469&sourceContentType=1&unitid=464706&webname=%E6%B1%9F%E8%A5%BF%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C&permissiontype=0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.jiangxi.gov.cn'
        header['Referer'] = 'http://www.jiangxi.gov.cn/col/col48469/index.html?uid=464706&pageNum=1'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        for url in start_url:
            yield scrapy.Request(url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):

        law_url_list = re.findall('href="([^"]+?)"', response.text)
        law_title_list = re.findall('" title="([^"]+?)"', response.text)
        law_time_list = re.findall('</a><b>([^<>]+?)</b>', response.text)

        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_time = tools.clean(law_time_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江西省"
        item["legalCategory"] = "江西省政府-规范性文件"
        item["legalPolicyName"] = response.meta['title']
        item["legalPublishedTime"] = response.meta['time']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = response.xpath('//*[@id="zoom"]').extract_first()
            fujian = response.xpath('//*[@id="zoom"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="zoom"]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//div[@class="artile_zw"]//table/tbody/tr[1]/td[3]').xpath('string(.)').extract_first()
            wenhao = tools.clean(wenhao)
            wenhao = wenhao.replace("文号:", "")

            if re.search("号", wenhao):
                item["legalDocumentNumber"] = wenhao

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
