import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import jieba.analyse

# 加载BERT模型和分词器
model_path = "model\\models--bert-base-chinese"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
model.eval()

# 读取CSV文件
df = pd.read_csv('after_process.csv', encoding='utf-8')

# 创建一个空列表以存储结果
results = []

# 遍历CSV文件中的每一行
for index, row in df.iterrows():
    text = row['comment']

    # 分词
    words = list(jieba.cut(text))

    # 关键词提取
    keywords = jieba.analyse.extract_tags(text, topK=5)  # 获取前5个关键词

    # 情感分析
    # 截断或填充文本以适应模型的期望长度
    inputs = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        sentiment = torch.softmax(outputs.logits, dim=1).tolist()[0]  # 情感分析结果

    results.append({'Text': text, 'Keywords': keywords, 'Sentiment': sentiment})

# 创建包含结果的新DataFrame
result_df = pd.DataFrame(results)

# 保存结果到CSV文件
result_df.to_csv('text_analysis_result.csv', index=False, encoding='utf-8')
