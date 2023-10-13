# -*- coding:utf-8 -*-
import scrapy
import time
import json
from lawScrapy import appbk_sql
from lawScrapy import tools
import logging
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)
# scrapy crawl country_laws_48_up


class CountryLaw48UpSpider(scrapy.Spider):
    name = 'country_laws_48_up'
    allowed_domains = ['miit.gov.cn']

    def start_requests(self):
        start_url = 'https://www.miit.gov.cn/search-front-server/api/search/info?websiteid=110000000000000&scope=basic&q=&pg=10&cateid=59&pos=title_text%2Cinfocontent%2Ctitlepy&_cus_eq_typename=&_cus_eq_publishgroupname=&_cus_eq_themename=&begin=&end=&dateField=deploytime&selectFields=title,content,deploytime,_index,url,cdate,infoextends,infocontentattribute,columnname,filenumbername,publishgroupname,publishtime,metaid,bexxgk,columnid,xxgkextend1,xxgkextend2,themename,typename,indexcode,createdate&group=distinct&highlightConfigs=%5B%7B%22field%22%3A%22infocontent%22%2C%22numberOfFragments%22%3A2%2C%22fragmentOffset%22%3A0%2C%22fragmentSize%22%3A30%2C%22noMatchSize%22%3A145%7D%5D&highlightFields=title_text%2Cinfocontent%2Cwebid&level=6&sortFields=%5B%7B%22name%22%3A%22deploytime%22%2C%22type%22%3A%22desc%22%7D%5D&p={}'

        for i in range(1, 18):
            yield scrapy.Request(start_url.format(str(i)), self.parse_dictionary, dont_filter=False, headers=tools.header)

    def parse_dictionary(self, response):
        res = json.loads(response.text)
        data_list = res['data']['searchResult']['dataResults']

        sql = "UPDATE `law` SET `legalPublishedTime` = '{}' WHERE legalUrl = '{}';"
        for i in data_list:
            tmpurl = i['groupData'][0]['data']['url']
            tmpurl = tools.getpath(tmpurl, response.url)
            law_time = time.strftime("%Y-%m-%d", time.localtime(int(i['groupData'][0]['data']['publishtime'])/1000))
            appbk_sql.mysql_com(sql.format(law_time, tmpurl))
