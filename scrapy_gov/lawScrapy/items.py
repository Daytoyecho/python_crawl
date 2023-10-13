# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LawscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    legalProvince = scrapy.Field()  # 部委和省市名
    legalCategory = scrapy.Field()  # 内容所属类别
    legalUrl = scrapy.Field()  # 法律网址
    legalPublishedTime = scrapy.Field()  # 法律发布日期
    legalDocumentNumber = scrapy.Field()  # 法律文号
    legalPolicyName = scrapy.Field()  # 法律名称
    legalPolicyText = scrapy.Field()  # 法律内容
    legalEnclosure = scrapy.Field()  # 法律附件
    legalEnclosureName = scrapy.Field()  # 法律附件名字
    legalEnclosureUrl = scrapy.Field()  # 法律附件链接
    legalScrapyTime = scrapy.Field()  # 抓取日期
    legalContent = scrapy.Field()  # 正文原始html
