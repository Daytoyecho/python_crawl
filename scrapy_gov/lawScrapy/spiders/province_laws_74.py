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
# scrapy crawl province_laws_74


class ProvinceLaw74Spider(scrapy.Spider):
    name = 'province_laws_74'
    allowed_domains = ['ah.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "https://www.ah.gov.cn/site/label/8888?IsAjax=1&_=0.5169706870968473&labelName=publicInfoList&siteId=6781961&pageSize=18&pageIndex={}&action=list&isDate=true&dateFormat=yyyy-MM-dd&length=50&organId=1681&type=4&catId=6708461&catIds=&cId=&keyWords=&result=%E6%9A%82%E6%97%A0%E7%9B%B8%E5%85%B3%E4%BF%A1%E6%81%AF&file=%2Fahxxgk%2Fxxgk%2FpublicInfoList_new_ah"

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for i in range(74):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        time.sleep(0.2)
        data_list = response.xpath('//*[@class="xxgk_navli"]//ul')
        for item in data_list:

            tmpurl = item.xpath('./li[1]/div/a/@href').extract_first()
            law_title = item.xpath('./li[1]/div/a/text()').extract_first()
            law_time = item.xpath('./li[2]/text()').extract_first()
            tmpurl = tools.getpath(tmpurl, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        if response.url in self.url_list:
            tools.MyException("与数据库重复")
        item["legalProvince"] = "安徽省"
        item["legalCategory"] = "安徽省政府-政府文件"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//*[contains(@class,"j-fontContent")]').extract_first()
            fujian = response.xpath('//*[contains(@class,"j-fontContent")]//a/@href').extract()
            fujian_name = response.xpath('//*[contains(@class,"j-fontContent")]//a[@href]').xpath('string(.)').extract()

            wenhao = response.xpath('//*[@id="zcjdDiv"]//tr[5]/td[1]/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = tools.clean(wenhao)

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
