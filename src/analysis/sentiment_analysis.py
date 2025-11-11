from transformers import pipeline
import re

# 文本清理函数
def clean_review_text(text):
    text = str(text)
    text = re.sub(r'http\S+', '', text) # 移除 URL
    text = re.sub(r'<[^>]+>', '', text)  # 移除 HTML 标签
    text = re.sub(r'@\w+', '', text)     # 移除 @ 提及
    text = re.sub(r'#\w+', '', text)     # 移除 # 标签
    text = text.strip()
    return text

class SentimentAnalyzer:
    """
    使用 Hugging Face (XLM-RoBERTa) 的高级情感分析器
    """
    def __init__(self):
        print("🤖 [SentimentAnalyzer] 正在加载 Transformer 模型...")
        # 这是一个强大的、多语言的情感分类模型
        # 它会返回 'Positive', 'Negative', 'Neutral'
        model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis", 
                model=model_name, 
                tokenizer=model_name,
                device=-1 # -1 表示使用 CPU (如果有 GPU 可以设为 0)
            )
            print("✅ [SentimentAnalyzer] 模型加载成功。")
        except Exception as e:
            print(f"❌ [SentimentAnalyzer] 模型加载失败: {e}")
            self.sentiment_pipeline = None

    def analyze(self, text):
        """
        对单条评论进行情感分析。
        
        返回:
        - score (float): 0.0 (负面) 到 1.0 (正面) 的标准分
        - label (str): 'negative', 'neutral', 'positive'
        """
        if not self.sentiment_pipeline:
            return 0.5, "neutral" # 模型加载失败时的回退

        try:
            # 1. 清理文本
            cleaned_text = clean_review_text(text)
            if not cleaned_text:
                return 0.5, "neutral"
            
            # 2. 截断文本 (Transformer 有 512 token 的限制)
            truncated_text = cleaned_text[:512]
            
            # 3. 运行模型
            result = self.sentiment_pipeline(truncated_text)[0]
            
            # 4. 解析结果
            label = result['label'].lower() # e.g., 'positive'
            model_score = result['score']   # 这是该标签的置信度 (0-1)
            
            # 5. 将 (label, model_score) 转换为标准分数 (0-1)
            #    0.0 = 极度负面, 0.5 = 中性, 1.0 = 极度正面
            if label == 'positive':
                standard_score = 0.5 + (model_score / 2.0)
            elif label == 'negative':
                standard_score = 0.5 - (model_score / 2.0)
            else: # neutral
                standard_score = 0.5
            
            return standard_score, label

        except Exception as e:
            print(f"❌ [SentimentAnalyzer] 分析时出错: {e}")
            return 0.5, "neutral"