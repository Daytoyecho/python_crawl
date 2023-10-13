# import requests

# header = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#     'Accept-Language': 'zh-CN,zh;q=0.9,rw;q=0.8',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36',
#     'Content-Type': 'application/json'
# }

# res = requests.get("http://www.sse.com.cn/aboutus/mediacenter/hotandd/s_index.htm", headers=header)
# res.encoding = "utf-8"
# print(res.text)
# import time


# res = time.strftime("%Y-%m-%d", time.localtime(1645718400))
# print(res)
import time
import string
import random
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import cv2
import pdfkit
import re
# text = """
# ;year[i]='2022';month[i]='04';day[i]='26';imgstrs[i]=' ';i++;urls[i]='/art/2022/4/22/art_2384_20220.html';headers[i]="北京市人民政府办公厅印发《关于继续加大中小微企业帮扶力度加快困难企业恢复发展的若干措施》的通知";year[i]='2022';month[i]='04';day[i]='22';imgstrs[i]=' ';i++;urls[i]='/art/2022/4/7/art_2384_17588.html';headers[i]="北京市人民政府办公厅印发《北京市关于支持外资研发中心设立和发展的规定》的通知";year[i]='2022';month[i]='04';day[i]='07';imgstrs[i]=' ';i++;urls[i]='/art/2022/3/16/art_2384_19864.html';headers[i]="北京市人民政府办公厅关于印发《北京市全民科学素质行动规划纲要(2021—2035年)》的通知";year[i]='2022';month[i]='03';day[i]='16';imgstrs[i]=' ';i++;urls[i]='/art/2021/12/15/art_2384_19872.html';headers[i]="北京市人民政府办公厅关于印发《北京市培育和激发市场主体活力持续优化营商环境实施方案》的通知";year[i]='2021';month[i]='12';day[i]='15';imgstrs[i]=' ';i++;urls[i]='/art/2021/11/24/art_2384_25990.html';headers[i]="中共北京市委 北京市人民政府关于印发《北京市“十四五”时期国际科技创新中心建设规划》的通知";year[i]='2021';month[i]='11';day[i]='24';
# """


# for i in re.findall(r"year\[i\]='([0-9]+)';month\[i\]='([0-9]+)';day\[i\]='([0-9]+)';", text):
#     print('-'.join(i))

url = "http://www.gd.gov.cn/attachment/0/369/369389/2532159.html"

# print(url[:url.rfind('?')])

# print(re.sub('src=".', 'src="123', url))

# n个台阶，我每次走1 2 3 4步，问我有多少种方法


# def a(n):
#     if n == 1:
#         return 1
#     if n == 2:
#         return 2
#     if n == 3:
#         return 4
#     if n == 4:
#         return 7
#     return a(n-1) + a(n-2) + a(n-3) + a(n-4)

def getpath(nowurl, baseurl):
    if nowurl[:4] == "http":
        return nowurl
    elif nowurl[0] == "/":
        return re.search(r'(https?://[^/]+?)/', baseurl).group(1) + nowurl
    elif nowurl[:3] == "../":
        return getpath(nowurl[3:], re.search(r'(https?://.+)/', baseurl).group(1))
    elif nowurl[:2] == "./":
        return re.search(r'(https?://.+)/', baseurl).group(1) + nowurl[1:]
    else:
        return re.search(r'(https?://.+)/', baseurl).group(1) + "/" + nowurl


# print(getpath("../../../../test1.png", url))
# print(getpath("../../../test2.png", url))
# print(getpath("../../test3.png", url))
# print(getpath("../test4.png", url))
# print(getpath("./test5.png", url))
# print(getpath("/test6.png", url))
# print(getpath("test7.png", url))
# print(getpath("http://www.gd.gov.cn/test8.png", url))


# test = 'src="../../abc.jpg" src=\'../abc.jpg\''

# for i in re.findall(r'src=[\'"](.*?)[\'"]', test):
#     src_url = getpath(i, url)
#     test = re.sub(r'src=[\'"]'+i+r'[\'"]', 'src="'+src_url+'"', test, count=1)
# print(test)

# def load_known_faces(dstImgPath, mtcnn, resnet):
#     aligned = []
#     knownImg = cv2.imread(dstImgPath)  # 读取图⽚
#     face = mtcnn(knownImg)  # 使⽤mtcnn检测⼈脸，返回【⼈脸数组】
#     if face is not None:
#         aligned.append(face[0])
#     aligned = torch.stack(aligned).to(device)
#     with torch.no_grad():
#         known_faces_emb = resnet(aligned).detach().cpu()  # 使⽤resnet模型 获取⼈脸对应的特征向量
#     return known_faces_emb, knownImg


# def match_faces(faces_emb, known_faces_emb, threshold):
#     isExistDst = False
#     distance = (known_faces_emb[0] - faces_emb[0]).norm().item()
#     if(distance < threshold):
#         isExistDst = True
#     return isExistDst


# if __name__ == '__main__':
#     # 获取设备
#     device = torch.device('cpu')
#     mtcnn = MTCNN(min_face_size=12, thresholds=[0.2, 0.2, 0.3], keep_all=True, device=device)

#     resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

#     MatchThreshold = 0.8
#     known_faces_emb, _ = load_known_faces('./lawScrapy/test1.jpg', mtcnn, resnet)

#     faces_emb, img = load_known_faces('./lawScrapy/test2.jpg', mtcnn, resnet)

#     isExistDst = match_faces(faces_emb, known_faces_emb, MatchThreshold)

#     if isExistDst:
#         boxes, prob, landmarks = mtcnn.detect(img, landmarks=True)
#         print('匹配')
#     else:
#         print('不匹配')
# test = """
# <div id="zoom">
#               <p><font>　　为进一步规范国有独资商业银行外汇业务市场准入监管，妥善解决历史遗留问题，理顺监管关系，现就恢复办理国有独资商业银行分支机构外汇业务市场准入审批手续的有关问题通知如下：</font></p>
#               <p><font>　　一、办理国有独资商业银行分支机构外汇业务审批手续，应按照“分清事实，分步恢复”的原则，由人民银行及其分支行依据《中国人民银行监管责任制》（银发［1999］140号）、《对国有独资商业银行一级分行本部监管职责分工的意见》（银发［1999］394号）等文件确定的监管权限具体审批。</font></p>
#               <p><font>　　二、办理审批手续的范围严格限定为：<br>　 （一）外汇业务市场准入审批工作移交人民银行之前，按照原外汇业务审批权限，外汇局已经同意对其擅自开办外汇业务的行为免于处罚，补办手续，但尚未办理具体审批手续的国有独资商业银行分支机构，人民银行凭原外汇局批复文件，受理其办理外汇业务审批手续的申请。<br>　 （二）经人民银行批准，由国有独资商业银行原国际业务部改建设立，但尚未在《金融机构营业许可证》中核准相应外汇业务范围的国有独资商业银行分支机构，人民银行分支行可受理其办理外汇业务审批手续的申请。</font></p>
#               <p><font>　　三、对其他未经批准，已擅自开办外汇业务或扩大外汇业务经营范围的国有独资商业银行分支机构，人民银行分支行根据其违规事实及情节轻重，依法对其擅自经营外汇业务的行为做出处理，并追究有关人员责任后，可受理其办理外汇业务审批手续的申请。</font></p>
#               <p><font>　　四、国有独资商业银行分支机构申请办理外汇业务审批手续，必须事先取得其总行或上级行的批准文件。申请办理审批手续的外汇业务种类，必须是其总行已经人民银行批准办理的外汇业务种类。</font></p>
#               <p><font>　　五、人民银行分支行对申请办理外汇业务审批手续的国有独资商业银行分支机构，应从实际需要出发，严格审核其外汇业务经营状况、管理状况及遵守法规情况；审核其是否具有健全的内控制度，是否具有开办外汇业务所必须的从业人员和设备。对经审核不符合办理外汇业务条件的国有独资商业银行分支机构，不予办理手续，并应要求限期进行清理整顿，直至停止办理外汇业务。<br>　　人民银行分支行对国有独资商业银行分支机构外汇业务审批文件，应同时抄报上一级人民银行备案。</font></p>
#               <p><font>　　六、国有独资商业银行分支机构在取得经营外汇业务批准文件后，必须在60日内到人民银行换领《金融机构营业许可证》。对逾期未办理换领手续的国有独资商业银行分支机构，原批准文件自动失效。</font></p>
#               <p><font>　　七、为进一步加强对国有独资商业银行的业务准入监管，总行正在着手制定《商业银行业务审批管理办法》。国有独资商业银行及其分支机构申请新开办外汇业务及扩大外汇业务范围的申请将在新《办法》下发后进行审批。</font></p>
#               <p align="right"><font>中国人民银行办公厅&nbsp;&nbsp;&nbsp; </font></p>
#               <p align="right"><font>二○○○年三月二十七日&nbsp;&nbsp; </font></p>
#              </div>

# """
# regex = ["\\", "(", ")", "{", "}", "+", "*", "[", "]", "?", "^", "$", ".", "|"]
# for i in re.findall(r'src=[\'"]([\s\S]+?)[\'"]', test):
#     if i[:5] == "data:":
#         continue
#     src_url = getpath(i, "http://www.pbc.gov.cn/tiaofasi/144941/144959/2808041/index.html")
#     tmp = i
#     for j in regex:
#         tmp = tmp.replace(j, "\\"+j)
#     print(tmp)
#     test = re.sub(r'src=[\'"]'+tmp+r'[\'"]', 'src="'+src_url+'"', test, count=1)
# print(test)

# test = """
# http://www.safe.gov.cn/safe/file/file/20170726/a6f0ff5744ff487ea23150bc1fdc7ff4.doc?n=%E7%94%B5%E5%AD%90%E9%93%B6%E8%A1%8C%E4%B8%AA%E4%BA%BA%E7%BB%93%E5%94%AE%E6%B1%87%E4%B8%9A%E5%8A%A1%E7%AE%A1%E7%90%86%E6%9A%82%E8%A1%8C%E5%8A%9E%E6%B3%95
# """


# def clean(words):
#     sub = re.sub(r'[\t\r\n\s]', '', words)
#     sub = sub.replace('\u3000', '').replace('\xa0', '')
#     sub = sub.replace('&nbsp;', '')
#     return sub


# def get_fujian_name(name, url, law_name):
#     tmpname = clean(name)
#     tmpname = "".join(re.findall(r'[\u4e00-\u9fa50-9a-zA-Z]+', tmpname))
#     if not tmpname:
#         return law_name + "附件.pdf", law_name+"附件"

#     if "?" not in url or re.search(r"(\.[a-zA-Z]+)", url[-6:]):
#         return tmpname + ''.join(random.sample(string.ascii_letters + string.digits, 8)) + re.search(r"(\.[a-zA-Z]+)", url[-6:]).group(1), tmpname
#     else:
#         tmpurl = url
#         tmpurl = tmpurl[:tmpurl.rfind('?')]
#         return tmpname + ''.join(random.sample(string.ascii_letters + string.digits, 8)) + re.search(r"(\.[a-zA-Z]+)", tmpurl[-6:]).group(1), tmpname


# file_name, name = get_fujian_name("巴啦啦小魔仙", test, "http://www.safe.gov.cn/safe/2016/1207/5669.html")
# print(file_name, name)
# law_time = time.strftime("%Y-%m-%d", time.localtime(int(1558688217000/1000)))
# tmpurl = "http://test.com"
# sql = "UPDATE `law` SET `legalPublishedTime` = '{}' WHERE legalUrl = '{}';"
# print(sql.format(law_time, tmpurl))

5
'''
n   1, a(n-1)+
    2, a(n-2)+
    3, a(n-3)+
    4, a(n-4)
'''


def a(n):
    if n == 1:
        return 1
    if n == 2:
        return 2
    if n == 3:
        return 4
    if n == 4:
        return 7

    return a(n-1)+a(n-2)+a(n-3)+a(n-4)
