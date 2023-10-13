# -*- coding:utf-8 -*-
import re
import os
import string
import random
import requests
from lawScrapy.ali_file import upload_file
import pdfkit
import json
import datetime
import time
import base64
import dateutil.tz as tz
header = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,rw;q=0.8',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
    # 'Content-Type': 'application/json'
}

regex = ["\\", "(", ")", "{", "}", "+", "*", "[", "]", "?", "^", "$", ".", "|"]


proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes(("H862E18G22168T4D" + ":" + "4C4B3FBE125D39FB"), "ascii")).decode("utf8")

a_bu_yun = {
    'http': 'http://H28791D6H5AW122D:D4BE8B845A1062E9@http-dyn.abuyun.com:9020',
    'https': 'http://H28791D6H5AW122D:D4BE8B845A1062E9@http-dyn.abuyun.com:9020'
}


def UTCTsToLocalDt(utcts):

    dt = datetime.datetime.fromtimestamp(utcts)

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    utc = dt.replace(tzinfo=from_zone)  # 先行替换datetime的时区到utc时区
    local = str(utc.astimezone(to_zone))
    return local[:10]


class MyException(Exception):
    pass


moban = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{}</title>
</head>
<body>
<center>
    <h1>{}</h1>
    <div id="middle">
        <span id="source" style="margin-right:16px">部委/省市：{}</span>
        <span id="publish_time">发布时间：{}</span>
    </div>
</center>
<div id="content" style="font-size: 20px;line-height: 32px;font-family: 'sans-serif';">{}</div>
</body>
</html>
"""


def get_name(name, url):
    tmp = "".join(re.findall(r'[\u4e00-\u9fa50-9a-zA-Z]+', name))
    if len(tmp) > 50:
        tmp = tmp[:50]
    file_name = tmp + \
        ''.join(random.sample(string.ascii_letters + string.digits, 8)) + '.pdf'

    # 如果有docx，就改成docx，否则看看有没有doc，目前已知会有这三种,第一个条件满足不会执行第二个，避免docx又被改成doc
    if re.search(r'\.docx', url, re.I):
        file_name = file_name[:-5]+'.docx'
    elif re.search(r'\.doc', url, re.I):
        file_name = file_name[:-4]+'.doc'

    if re.search(r'\.xlsx', url, re.I):
        file_name = file_name[:-5]+'.xlsx'
    elif re.search(r'\.xls', url, re.I):
        file_name = file_name[:-4]+'.xls'

    if re.search(r'\.wps', url, re.I):
        file_name = file_name[:-4]+'.wps'

    if re.search(r'\.tif', url, re.I):
        file_name = file_name[:-4]+'.tif'

    if re.search(r'\.zip', url, re.I):
        file_name = file_name[:-4]+'.zip'

    if re.search(r'\.rar', url, re.I):
        file_name = file_name[:-4]+'.rar'

    if re.search(r'\.ceb', url, re.I):
        file_name = file_name[:-4]+'.ceb'

    if re.search(r'\.txt', url, re.I):
        file_name = file_name[:-4]+'.txt'
    return file_name


def replace_content(title, source, time, content, law_url):
    tmp_content = re.sub(r'font\-family', r"abc", content, flags=re.I)
    tmp_content = re.sub(r'<script[\s\S]+?</script>', r"", tmp_content, flags=re.I)
    tmp_content = re.sub(r'<style[\s\S]+?</style>', r"", tmp_content, flags=re.I)
    tmp_content = re.sub(r'face=', r"abc=", tmp_content, flags=re.I)
    tmp_content = moban.format(title, title, source, time, tmp_content)
    tmp_content = re.sub(r'@font\-face', r"abc", tmp_content, flags=re.I)

    for i in re.findall(r'src=[\'"](.+?)[\'"]', tmp_content):
        if i[:4] == "http":
            continue
        if i[:5] == "data:":
            continue
        src_url = getpath(i, law_url)
        tmp = i
        for j in regex:
            tmp = tmp.replace(j, "\\"+j)
        tmp_content = re.sub(r'src=[\'"]'+tmp+r'[\'"]', 'src="'+src_url+'"', tmp_content, count=1)

    # tmp_content = re.sub('<img', '<img style="width:80%"', tmp_content)
    return tmp_content


def get_fujian_name(name, url, law_name):
    tmpname = clean(name)
    tmpname = "".join(re.findall(r'[\u4e00-\u9fa50-9a-zA-Z]+', tmpname))
    if not tmpname:
        tmpname = law_name

    if "?" not in url or re.search(r"(\.[a-zA-Z]+)", url[-6:]):
        return tmpname + ''.join(random.sample(string.ascii_letters + string.digits, 8)) + re.search(r"(\.[a-zA-Z]+)", url[-6:]).group(1), tmpname
    else:
        tmpurl = url
        tmpurl = tmpurl[:tmpurl.rfind('?')]
        return tmpname + ''.join(random.sample(string.ascii_letters + string.digits, 8)) + re.search(r"(\.[a-zA-Z]+)", tmpurl[-6:]).group(1), tmpname


def get_PDF_lawPolicyText(url, file_name):
    time.sleep(2)
    res = requests.get(url, headers=header,  timeout=60)
    with open(file_name, 'wb')as f:
        f.write(res.content)
        if file_name[-4:] != ".txt" and os.path.getsize(file_name)/1024 < 4:
            raise MyException("附件太小")


def isWeb(url):
    if not re.search(r'\.doc', url, re.I) and not re.search(r'\.xls', url, re.I)\
            and not re.search(r'\.pdf', url, re.I) and not re.search(r'\.wps', url, re.I)\
            and not re.search(r'\.zip', url, re.I) and not re.search(r'\.jpg', url, re.I)\
            and not re.search(r'\.png', url, re.I) and not re.search(r'\.rar', url, re.I)\
            and not re.search(r'\.tif', url, re.I) and not re.search(r'\.ceb', url, re.I)\
            and not re.search(r'\.txt', url, re.I):
        return True
    return False


def clean(words):
    sub = re.sub(r'[\t\r\n\s]', '', words)
    sub = sub.replace('\u3000', '').replace('\xa0', '')
    sub = sub.replace('&nbsp;', '')
    return sub


def getpath(nowurl, url):
    baseurl = url
    if "?" in url:
        baseurl = url[:url.rfind('?')]
    if nowurl[:4] == "http":
        return nowurl
    elif nowurl[0] == "/":
        return re.search(r'(https?://[^/]+?)/', baseurl).group(1) + nowurl
    elif nowurl[:3] == "../":
        return getpath(nowurl[3:], re.search(r'(https?://.+)/', baseurl).group(1))
    elif nowurl[:2] == "./":
        return re.search(r'(https?://.+)/', baseurl).group(1) + nowurl[1:]
    elif nowurl[0] == "?":
        return baseurl + nowurl
    else:
        return re.search(r'(https?://.+)/', baseurl).group(1) + "/" + nowurl


def xaizaifujian(fujian_url, fujian_name, law_name, law_url):
    law_file = []
    law_file_name = []
    law_file_url = []
    for i in range(len(fujian_url)):
        if not fujian_url[i] or len(fujian_url[i]) < 4:
            continue
        url = getpath(fujian_url[i], law_url)
        if not isWeb(url):
            if not fujian_name[i]:
                continue
            file_name, name = get_fujian_name(fujian_name[i], url, law_name)
            try:
                get_PDF_lawPolicyText(url, file_name)
            except Exception as e:
                print("*************附件下载错误:{}--{}--***************".format(law_url, e))
                continue
            file_oss_url = upload_file(file_name, "avatar", file_name)
            law_file_name.append(name)
            law_file.append(file_oss_url)
            law_file_url.append(url)

    return json.dumps(law_file, ensure_ascii=False), json.dumps(law_file_name, ensure_ascii=False), json.dumps(law_file_url, ensure_ascii=False)


def xaizaizw(title, source, time, content, pdf_name, law_url):

    if not content:
        raise MyException("*************正文没有取到:{}***************".format(law_url))
    tmpcontent = replace_content(title, source, time, content, law_url)
    try:
        pdfkit.from_string(tmpcontent, pdf_name)
    except Exception as e:
        print("*************正文下载错误:{}--{}--***************".format(law_url, e))


def xaizai_not_html_zw(pdf_name, body):
    with open(pdf_name, 'wb')as f:
        f.write(body)


def getnowtime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
