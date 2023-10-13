import pandas as pd
import re

# 读取原始CSV文件
original_data = pd.read_csv('weibo_data.csv')

# 去重操作
deduplicated_data = original_data.drop_duplicates().copy()

# 数据清洗
processed_comments = []  # 用于存储处理后的文本

for text in deduplicated_data['comment']:
    txt = str(text)
    # 使用正则去除话题
    txt = re.sub(r'#[^#]*#', '', txt)
    # 去除其他多余字符
    txt = txt.replace('"', '').replace('、', '')
    processed_comments.append(txt)

# 覆盖原始 DataFrame 中的 'comment' 列
deduplicated_data['comment'] = processed_comments

# 使用正则表达式去除双引号 "" 形式的空行
deduplicated_data['comment'] = deduplicated_data['comment'].str.replace(r'^""$','')

# 删除所有空行
deduplicated_data = deduplicated_data[deduplicated_data['comment'] != '']

# 保存处理后的数据到新的CSV文件
deduplicated_data.to_csv('after_process.csv', index=False)

print("去重和文本处理完成并保存为新的CSV文件。")