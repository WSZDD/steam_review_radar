# sentiment.py
from paddlenlp import Taskflow

# 初始化中文情感分析模型
senta = Taskflow("sentiment_analysis")

def analyze_sentiment(text):
    """
    输入：一段中文文本
    输出：情感标签（'positive' 或 'negative'）和置信度
    """
    result = senta(text)[0]
    return result['label'], result['score']

# 统计情感数据并返回，以生成统计图
def sentiment_statistics(reviews):
    """
    输入：包含评论文本的列表
    输出：情感统计数据字典
    """
    stats = {'positive': 0, 'negative': 0}
    for review in reviews:
        label, _ = analyze_sentiment(review)
        stats[label] += 1
    return stats