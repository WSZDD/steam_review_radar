import jieba
import re
import pandas as pd
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

# --- 1. 加载停用词 ---
def _load_stopwords(filepath="static/cn_stopwords.txt"): #
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            stopwords = {line.strip() for line in f}
            # 为 BERTopic 添加一些额外的常见噪音词
            stopwords.update(["游戏", "这个", "真的", "没有", "一个", "就是", "什么", "不是", "但是", "可以", "感觉"])
            return list(stopwords)
    except FileNotFoundError:
        print("⚠️ 未找到停用词表")
        return []

stopwords = _load_stopwords()

# --- 2. 文本预处理函数 ---
def _clean_text(text):
    text = re.sub(r'<[^>]+>', '', str(text)) # 移除 HTML
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', ' ', text) # 只保留中英文和空格
    text = text.strip()
    return text

# --- 3. Jieba 分词器 (用于 BERTopic) ---
# BERTopic 需要一个分词器来处理中文
def _jieba_tokenizer(text):
    return jieba.lcut(text)

# --- 4. 核心分析函数 (BERTopic 版) ---

# BERTopic 模型和嵌入模型是昂贵资源，全局加载一次
# 我们将使用一个轻量级但高效的多语言模型
print("正在加载 SentenceTransformer 模型 (paraphrase-multilingual-MiniLM-L12-v2)...")
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("模型加载完毕。")

def analyze_with_bertopic(reviews_series):
    """
    使用 BERTopic 进行语义主题分析
    返回: (topic_map, echarts_word_data)
    """
    if reviews_series.empty:
        return {}, []

    print("BERTopic 开始分析...")
    # 1. 准备数据：清理文本
    docs = reviews_series.apply(_clean_text).tolist()

    # 2. 准备 BERTopic 的中文环境
    # 我们需要一个 CountVectorizer 来处理分词和停用词
    vectorizer_model = CountVectorizer(tokenizer=_jieba_tokenizer, stop_words=stopwords)

    # 3. 初始化 BERTopic
    # min_topic_size=5 意味着一个主题至少要包含 5 篇评论
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        language="multilingual",
        min_topic_size=5,
        top_n_words=20,
        calculate_probabilities=False,
        verbose=True
    )

    # 4. 训练模型 (这是最慢的一步)
    # BERTopic 会自动处理降维 (UMAP) 和聚类 (HDBSCAN)
    try:
        topics, _ = topic_model.fit_transform(docs)
        # 在训练后，立即获取代表性评论
        representative_docs = topic_model.get_representative_docs()
    except Exception as e:
        print(f"❌ BERTopic 训练失败: {e}")
        return {}, []

    print("BERTopic 训练完成。正在提取主题和摘要...")

    topic_map = {}
    echarts_word_data = []
    topic_info = topic_model.get_topic_info()
    
    # --- 3. 修改循环，构建新的 topic_map ---
    for _, row in topic_info[topic_info.Topic != -1].iterrows():
        topic_id = int(row.Topic)
        
        # --- a. 构建 topic_map (包含关键词和摘要) ---
        all_words_scores = topic_model.get_topic(topic_id) 
        
        # 提取关键词
        keywords = [w[0] for w in all_words_scores[:7] if w[0] and w[0].strip()]
        keywords_str = "、".join(keywords)
        
        # 提取代表性摘要 (即“一句话概括”)
        summary = "暂无代表性评论。" # 默认值
        if topic_id in representative_docs:
            summary = representative_docs[topic_id][0] # 取最典型的那一条
            # 清理和截断摘要
            summary = _clean_text(summary)
            if len(summary) > 100:
                summary = summary[:100] + "..."
        
        # 存入新的结构
        topic_map[topic_id] = {
            "keywords": keywords_str,
            "summary": summary
        }

        # --- b. 构建 echarts_word_data (逻辑不变) ---
        words_scores = all_words_scores
        if words_scores:
            for word, score in words_scores:
                word_value = max(int(score * 1000), 1)
                echarts_word_data.append({
                    "name": word,
                    "value": word_value,
                    "topic_id": topic_id
                })

    print(f"BERTopic 分析完毕。找到 {len(topic_map)} 个有效主题。")
    return topic_map, echarts_word_data