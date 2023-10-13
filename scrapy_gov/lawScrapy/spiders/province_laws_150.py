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

# scrapy crawl province_laws_150


class ProvinceLaw150Spider(scrapy.Spider):
    name = 'province_laws_150'
    allowed_domains = ['nmg.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        base = "https://www.nmg.gov.cn/zwgk/zfxxgk/zfxxgkml/gzxzgfxwj/xzgfxwj/index_{}.html"
        start_url = ['https://www.nmg.gov.cn/zwgk/zfxxgk/zfxxgkml/gzxzgfxwj/xzgfxwj/index.html']

        for i in range(1, 77):
            start_url.append(base.format(str(i)))

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        for url in start_url:
            yield scrapy.Request(url, self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):

        law_url_list = response.xpath('//*[@id="table1"]/tbody/tr/td[2]/a/@href').extract()
        law_time = response.xpath('//*[@id="table1"]/tbody/tr/td[6]/text()').extract()

        for i in range(len(law_url_list)):
            tmpurl_0 = law_url_list[i]
            tmpurl = tools.getpath(tmpurl_0, response.url)
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"time": law_time[i]}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "内蒙古自治区"
        item["legalCategory"] = "内蒙古自治区政府-行政规范性文件"

        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="ql_detailbro_content qgl_fontsize_box"]').extract_first()
            fujian = response.xpath('//div[@class="ql_detailbro_content qgl_fontsize_box"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="ql_detailbro_content qgl_fontsize_box"]//a[@href]').xpath('string(.)').extract()
            # 处理名字
            name = response.xpath('//h1[@class="ql_detailbro_title"]//text()').extract()
            if name:
                name_tmp = ""
                for i in range(len(name)):
                    name_tmp += tools.clean(name[i])
                item["legalPolicyName"] = name_tmp
            else:
                item["legalPolicyName"] = ""
            # 处理文号
            wenhao = response.xpath('//table[@class="ql_detailbro_table"]//tr[2]/td[4]/text()').extract_first()
            if wenhao:
                item["legalDocumentNumber"] = wenhao
            else:
                item["legalDocumentNumber"] = ""

            pdf_name = tools.get_name(item["legalPolicyName"], response.url)

            item['legalContent'] = content
            tools.xaizaizw(item["legalPolicyName"], item["legalProvince"], item["legalPublishedTime"], content, pdf_name, response.url)

        item["legalPolicyText"] = upload_file(pdf_name, "avatar", pdf_name)
        legal_enclosure, legal_enclosure_name, legal_enclosure_url = tools.xaizaifujian(fujian, fujian_name, item["legalPolicyName"], response.url)
        if legal_enclosure != "[]":
            item["legalEnclosure"] = legal_enclosure
            item["legalEnclosureName"] = legal_enclosure_name
            item["legalEnclosureUrl"] = legal_enclosure_url
        item['legalScrapyTime'] = tools.getnowtime()
        return item
