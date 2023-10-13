# -*- coding:utf-8 -*-
import scrapy
from lawScrapy.items import LawscrapyItem
import re
import time
import json
from lawScrapy.ali_file import upload_file
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_48


class CountryLaw48Spider(scrapy.Spider):
    name = 'country_laws_48'
    allowed_domains = ['miit.gov.cn']
    url_list = []
    wrong = 0
    count = 0

    def start_requests(self):
        start_url = 'https://www.miit.gov.cn/search-front-server/api/search/info?websiteid=110000000000000&scope=basic&q=&pg=10&cateid=59&pos=title_text%2Cinfocontent%2Ctitlepy&_cus_eq_typename=&_cus_eq_publishgroupname=&_cus_eq_themename=&begin=&end=&dateField=deploytime&selectFields=title,content,deploytime,_index,url,cdate,infoextends,infocontentattribute,columnname,filenumbername,publishgroupname,publishtime,metaid,bexxgk,columnid,xxgkextend1,xxgkextend2,themename,typename,indexcode,createdate&group=distinct&highlightConfigs=%5B%7B%22field%22%3A%22infocontent%22%2C%22numberOfFragments%22%3A2%2C%22fragmentOffset%22%3A0%2C%22fragmentSize%22%3A30%2C%22noMatchSize%22%3A145%7D%5D&highlightFields=title_text%2Cinfocontent%2Cwebid&level=6&sortFields=%5B%7B%22name%22%3A%22deploytime%22%2C%22type%22%3A%22desc%22%7D%5D&p={}'

        res = appbk_sql.mysql_com('SELECT legalUrl FROM `law`; ')
        self.url_list = [item['legalUrl'] for item in res]
        for i in range(1, 18):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=True, headers=tools.header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['data']['searchResult']['dataResults']

        for i in data_list:
            tmpurl = i['groupData'][0]['data']['url']
            tmpurl = tools.getpath(tmpurl, response.url)
            law_title = i['groupData'][0]['data']['title']
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(i['groupData'][0]['data']['publishtime'])/1000))
            self.count += 1
            print(self.count)
            if tmpurl not in self.url_list:
                yield scrapy.Request(tmpurl, self.parse_article, meta={"title": law_title, 'time': law_time}, dont_filter=True, headers=tools.header)

    def parse_article(self, response):
        item = LawscrapyItem()
        item["legalUrl"] = response.url
        item["legalProvince"] = "中华人民共和国工业和信息化部"
        item["legalCategory"] = "中华人民共和国工业和信息化部-法律法规"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []
        if tools.isWeb(response.url):
            try:
                ti = response.xpath('//*[@id="con_time"]').xpath('string(.)').extract_first()[5:15]
                item["legalPublishedTime"] = tools.clean(ti)
            except:
                print("时间取错")
            content = response.xpath('//*[@id="con_con"]').extract_first()
            fujian = response.xpath('//*[@id="con_con"]//a/@href').extract()
            fujian_name = response.xpath('//*[@id="con_con"]//a[@href]').xpath('string(.)').extract()
            try:
                tmpn = response.xpath('//*[@id="con_con"]/p[2]').xpath('string(.)').extract_first()
                if re.search(r"第[^<>]{1,5}号", tools.clean(tmpn)):
                    tmpn = response.xpath('//*[@id="con_con"]/p[1]').xpath('string(.)').extract_first() + tmpn
                    item["legalDocumentNumber"] = tools.clean(tmpn)
            except:
                pass
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
