# analysis/sentiment_analysis.py
from snownlp import SnowNLP
import pandas as pd

def analyze_sentiment(df):
    """
    输入: 评论DataFrame，必须包含 'content' 列
    输出: 添加情感分析列 ['sentiment_score', 'sentiment_label']
    """
    def sentiment_score(text):
        try:
            s = SnowNLP(text)
            return s.sentiments
        except:
            return 0.5  # 失败时中性

    df['sentiment_score'] = df['content'].apply(sentiment_score)

    def label(score):
        if score > 0.6:
            return '正向'
        elif score < 0.4:
            return '负向'
        else:
            return '中性'

    df['sentiment_label'] = df['sentiment_score'].apply(label)

    sentiment_summary = df['sentiment_label'].value_counts().to_dict()

    return df, sentiment_summary
