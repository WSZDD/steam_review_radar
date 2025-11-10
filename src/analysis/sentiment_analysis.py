# src/analyzer/sentiment_analysis.py
import re
from snownlp import SnowNLP

class SentimentAnalyzer:


    def preprocess(self, text: str) -> str:
        """清理文本"""
        text = re.sub(r"http\S+", "", text)      # 去掉URL
        text = re.sub(r"<.*?>", "", text)        # 去掉HTML标签
        text = re.sub(r"\s+", " ", text).strip() # 去掉多余空格
        return text



    def get_sentiment_score(self, text: str) -> float:
        """返回统一到0~1的情感分数"""
        text = self.preprocess(text)
        if not text:
            return 0.5  # 空评论视为中性
        score = SnowNLP(text).sentiments  # 0~1

        return score

    def get_sentiment_label(self, score: float) -> str:
        """根据分数分类"""
        if score >= 0.6:
            return "positive"
        elif score <= 0.4:
            return "negative"
        else:
            return "neutral"
