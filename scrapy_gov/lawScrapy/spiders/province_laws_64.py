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
# scrapy crawl province_laws_64


class ProvinceLaw64Spider(scrapy.Spider):
    name = 'province_laws_64'
    allowed_domains = ['jinan.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://www.jinan.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=70&perpage=25"

        baseform = "col=1&webid=1&path=http%3A%2F%2Fwww.jinan.gov.cn%2F&columnid=85285&sourceContentType=1&unitid=564862&webname=%25E6%25B5%258E%25E5%258D%2597%25E5%25B8%2582%25E4%25BA%25BA%25E6%25B0%2591%25E6%2594%25BF%25E5%25BA%259C&permissiontype=0"
        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.jinan.gov.cn/col/col85285/index.html?uid=564862&pageNum=3'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        yield scrapy.Request(start_url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('<a href="([^"]+?)" target="_blank" class="biao_a">', response.text)
        law_title_list = re.findall('class="biao_a">(.+?)</a>', response.text)
        law_text_list = re.findall('target="_blank" class="beizhu_a">(.+?)</a>', response.text)
        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            law_text = tools.clean(law_text_list[i])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "text": law_text}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "山东省"
        item["legalCategory"] = "济南市政府-规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])

        if re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']):
            tmp_time = re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']).group(1)
            item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time.strip(), "%Y年%m月%d日"))

            # 处理文号
        if re.search(r'日([\S]+?[0-9]{0,4}号)', tools.clean(response.meta['text'])):
            item["legalDocumentNumber"] = re.search(r'日([\S]+?[0-9]{0,4}号)', tools.clean(response.meta['text'])).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.xpath('//div[@class="wz_zhuti"]').extract_first()
            fujian = response.xpath('//div[@class="wz_zhuti"]//a/@href').extract()
            fujian_name = response.xpath('//div[@class="wz_zhuti"]//a[@href]').xpath('string(.)').extract()

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
