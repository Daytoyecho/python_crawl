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
# scrapy crawl province_laws_117


class ProvinceLaw117Spider(scrapy.Spider):
    name = 'province_laws_117'
    allowed_domains = ['jiangxi.gov.cn']

    url_list = []
    count = 0

    def start_requests(self):

        start_url = ["http://www.jiangxi.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=114&perpage=114"]

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]

        baseform = "col=1&webid=3&path=http%3A%2F%2Fwww.jiangxi.gov.cn%2F&columnid=64511&sourceContentType=3&unitid=464148&webname=%E6%B1%9F%E8%A5%BF%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C&permissiontype=0"
        header = deepcopy(tools.header)
        header['Origin'] = 'http://www.jiangxi.gov.cn'
        header['Referer'] = 'http://www.jiangxi.gov.cn/col/col64511/index.html'
        header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        for url in start_url:
            yield scrapy.Request(url, body=baseform, method='POST', callback=self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):
        law_url_list = re.findall('<h1><a href="([^"]+?)">', response.text)
        law_title_list = re.findall('<h1><a [^<>]*?>(.*?)</a>', response.text)
        text_list = re.findall('<h2>([^<>]*?)</h2>', response.text)

        for i in range(len(law_url_list)):
            tmpurl = law_url_list[i]
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = tools.clean(law_title_list[i])
            tmp_text = tools.clean(text_list[i])

            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(0.2)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "text": tmp_text}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "江西省"
        item["legalCategory"] = "江西省政府-规章"
        item["legalPolicyName"] = response.meta['title']
        # 处理时间
        if re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']):
            tmp_time = re.search(r'([0-9]{0,4}年[0-9]{0,2}月[0-9]{0,2}日)', response.meta['text']).group(1)
        item["legalPublishedTime"] = time.strftime("%Y-%m-%d", time.strptime(tmp_time.strip(), "%Y年%m月%d日"))

        # 处理文号
        if re.search(r'(江西省.*?[0-9]{0,4}号)', response.meta['text']):
            item["legalDocumentNumber"] = re.search(r'(江西省.*?[0-9]{0,4}号)', response.meta['text']).group(1)

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):

            content = re.search(r'<meta name="ContentStart"/>([\s\S]+?)<meta name="ContentEnd"/>', response.text).group(1)
            fujian = re.findall(r'href="([^"]+?)"', content)
            fujian_name = re.findall(r'href="[^"]+?"[^>]*>([\s\S]+?)</a>', content)
            for i in range(len(fujian_name)):
                fujian_name[i] = tools.clean(re.sub(r'<[^<>]+?>', '', fujian_name[i]))

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
