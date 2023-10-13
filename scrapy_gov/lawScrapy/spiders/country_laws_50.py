# -*- coding:utf-8 -*-
from copy import deepcopy
from email import header
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
# scrapy crawl country_laws_50


class CountryLaw50Spider(scrapy.Spider):
    name = 'country_laws_50'
    allowed_domains = ['most.gov.cn']
    url_list = []
    count = 0

    def start_requests(self):
        start_url = 'http://www.moj.gov.cn/policyManager/policy/getPolicyDocList'

        res = appbk_sql.mysql_com(
            'SELECT legalUrl FROM `law` where legalUrl LIKE "http://www.moj.gov.cn/%"; ')
        self.url_list = [item['legalUrl'] for item in res]

        formdata = [{
            'file_status': "1",
            'file_type': 1,
            'pageNum': 1,
            'pageSize': 15,
            'searchType': 1,
            'skipPage': "",
            'validity': 1
        }]

        base = {
            'file_status': "1",
            'file_type': 1,
            'pageNum': "",
            'pageSize': 15,
            'searchType': 1,
            'skipPage': "",
            'totalPage': 4,
            'validity': 1
        }

        for i in range(2, 5):
            tmp = deepcopy(base)
            tmp['pageNum'] = str(i)
            formdata.append(tmp)
        header = tools.header
        header['Content-Type'] = "application/json;charset=UTF-8"
        for data in formdata:
            yield scrapy.Request(start_url, body=json.dumps(data), method='POST', callback=self.parse_dictionary, dont_filter=True, headers=header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['list']
        BASEURL = 'http://www.moj.gov.cn/policyManager/policy/getPolicyDocDetail'

        baseform = {
            'file_status': "1",
            'file_type': 1,
            'pageNum': 1,
            'pageSize': 15,
            'pkid': "",
            'searchType': 1,
            'skipPage': "",
            'validity': 1
        }
        header = tools.header
        header['Content-Type'] = "application/json;charset=UTF-8"
        for item in data_list:
            tmpform = deepcopy(baseform)
            tmpform['pkid'] = item["aritcleid"]
            law_title = item['document_title']
            law_time = item['release_date']
            law_document_number = item['post_number']
            self.count += 1
            print(self.count)
            yield scrapy.Request(BASEURL, body=json.dumps(tmpform), method='POST', callback=self.parse_article, meta={"title": law_title, 'time': law_time, 'documentNumber': law_document_number, 'pkid': tmpform['pkid']}, dont_filter=True, headers=header)

    def parse_article(self, response):
        base_fujian = "http://www.moj.gov.cn/policyManager/attach/downloadFile?realfilename={}"
        base_article_url = "http://www.moj.gov.cn/policyManager/regulationDetail.html?showMenu=false&showFileType=1&pkid={}"
        res = json.loads(response.text)
        item = LawscrapyItem()
        item["legalUrl"] = base_article_url.format(response.meta['pkid'])
        item["legalProvince"] = "中华人民共和国司法部"
        item["legalCategory"] = "司法部-规章"
        item["legalPolicyName"] = tools.clean(response.meta['title'])
        item["legalPublishedTime"] = tools.clean(response.meta['time'])
        item["legalDocumentNumber"] = tools.clean(response.meta['documentNumber'])

        pdf_name = tools.get_name(item["legalPolicyName"], response.url)
        fujian = []
        fujian_name = []

        content = res['data']['document_content']
        fujian_list = res['data']['policeFilesList']
        for i in fujian_list:
            fujian.append(base_fujian.format(i['_id']))
            fujian_name.append(i['filename'])
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
