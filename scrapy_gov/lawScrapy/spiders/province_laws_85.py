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
# scrapy crawl province_laws_85


class ProvinceLaw85Spider(scrapy.Spider):
    name = 'province_laws_85'
    allowed_domains = ['csrc.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):

        start_url = "http://www.csrc.gov.cn/searchList/67fd04488654475eadd7b94ee8e12502?_isAgg=true&_isJson=true&_pageSize=10&_template=index&_rangeTimeGte=&_channelName=&page={}"

        header = deepcopy(tools.header)
        header['Referer'] = 'http://www.csrc.gov.cn/hubei/c104401/zfxxgk_zdgk.shtml?channelid=67fd04488654475eadd7b94ee8e12502'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 16):
            time.sleep(2)
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=False, headers=header)

    def parse_dictionary(self, response):

        data = json.loads(response.text)

        for item in data['data']['results']:
            tmpurl = item['url']
            tmpurl = tools.getpath(tmpurl, "http://www.csrc.gov.cn/hubei/c104401/zfxxgk_zdgk.shtml")
            law_title = item['title']
            law_time = item['publishedTimeStr'][:10]
            law_content = item['contentHtml']
            law_number = ""
            for i in item['domainMetaList'][0]['resultList']:
                if i['name'] == "文号" and i['value']:
                    law_number = tools.clean(i['value'])
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                time.sleep(1)
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, "time": law_time, 'content': law_content, 'number': law_number}, dont_filter=False, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "湖北省"
        item["legalCategory"] = "中国证券监督管理委员会湖北监管局-通知公告"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        if response.meta['number']:
            item["legalDocumentNumber"] = response.meta['number']

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            content = response.meta['content']
            fujian = re.findall(r'<a[^<>]+?href="([^"]+?)"', content)
            fujian_name = re.findall(r'<a[^<>]+?>([\s\S]+?)</a>', content)
            content = re.sub(
                r'<table[^<>]+?>', '<table style="border-collapse: collapse; margin: 0px auto; border: none;" class="FCK__ShowTableBorders2" border="0" cellspacing="0" cellpadding="0" align="center">', content, flags=re.I)
            content = '<div style="position: relative;width:100%">' + content + '</div>'
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
