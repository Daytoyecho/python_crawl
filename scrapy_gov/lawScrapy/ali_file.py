#!/usr/bin/env python3
# coding=utf-8
# 阿里云oss功能
import json
import os
import sys
import time
import json
import oss2
import requests
import logging
from oss2 import logger
logger.setLevel(logging.WARNING)
# 阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户。
auth = oss2.Auth('LTAI5t9Teaodt7cYKdTAWv9N', 'DDTvPQYILWpB21IrHacOeA2lcBIM4e')
# yourEndpoint填写Bucket所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint填写为https://oss-cn-hangzhou.aliyuncs.com。
# 填写Bucket名称。
bucket = oss2.Bucket(auth, 'http://oss-cn-hongkong.aliyuncs.com', 'cata')
base_url = "https://cata.oss-cn-hongkong.aliyuncs.com/"


"""
功能:上传本地文件
输入:local_file, 本地文件名
输入:path, oss上的路径,需要预先设置
输入:filename, oss上文件命名
返回:上的url
"""


def upload_file(local_file, path, filename):
    # 读取文件
    f = open(local_file, 'rb')
    text = f.read()

    # 上传
    bucket.put_object(path + "/" + filename, text)
    f.close()
    oss_url = base_url + path + "/" + filename
    return oss_url


"""
功能:上传本地文件到腾讯oss
输入:file_bin, 二进制文件流
输入:path, oss上的路径,需要预先设置
输入:filename, oss上文件命名
返回:腾讯云上的url
"""


def upload_stream(file_bin, path, filename):
    bucket.put_object(path + "/" + filename, file_bin)
    oss_url = base_url + path + "/" + filename
    return oss_url


"""
功能:上传url图片
输入:url, 图片或者文件url,需要下载并上传的
输入:path, oss上的路径,需要预先设置
输入:filename, oss上文件命名
返回:云上的url
"""


def upload(url, path, filename):
    # 下载文件
    header = {}
    header["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    res = requests.get(url, headers=header)

    # 如果仍是错误,返回错误
    if 200 != res.status_code:
        print("ERROR:file download error")
        return -1

    # 填写Object完整路径。Object完整路径中不能包含Bucket名称。
    bucket.put_object(path + "/" + filename, res)
    oss_url = base_url + path + "/" + filename
    return oss_url
