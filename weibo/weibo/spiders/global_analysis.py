import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import jieba.analyse
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

# 设置字体以支持中文字符
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体

# 加载BERT模型和分词器
model_path = "model\\models--bert-base-chinese"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path)
model.eval()

# 读取CSV文件
df = pd.read_csv('after_process.csv', encoding='utf-8')

# 合并所有文本并提取关键词
combined_text = ' '.join(df['comment'].tolist())
keywords = jieba.analyse.extract_tags(combined_text, topK=30, withWeight=True)

# 打印测试
# for word, weight in keywords:
#     print(f'{word}: {weight}')

# 创建词云对象
wordcloud = WordCloud(
    font_path='c:\windows\Fonts\STZHONGS.TTF',
    width=800,
    height=400,
    mode="RGBA",
    background_color='white'
)

# 使用关键词和权重来生成词云
wordcloud.generate_from_frequencies(dict(keywords))

# 显示词云图
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title('Keywords Word Cloud')
plt.show()

# 绘制词频图
words, word_counts = zip(*keywords)
plt.barh(range(len(words)), word_counts, align='center')
plt.yticks(range(len(words)), words)
plt.xlabel('词频')
plt.title('Keywords Word Frequency')
# 自动调整布局避免重叠
plt.tight_layout()

plt.show()


# 情感分析
# 截断或填充文本以适应模型的期望长度
inputs = tokenizer(combined_text, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    sentiment = torch.softmax(outputs.logits, dim=1).tolist()[0]  # 情感分析结果

# 创建包含结果的新DataFrame
result_df = pd.DataFrame({'Keywords': [keywords], 'Sentiment': [sentiment]})

# 保存结果到CSV文件
result_df.to_csv('global_text_analysis_result.csv', index=False, encoding='utf-8')