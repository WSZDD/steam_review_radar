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
            # 1. 从文件加载，并过滤掉空行
            stopwords = {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        print("⚠️ 未找到停用词表，使用内置列表。")
        stopwords = set()
    
    game_specific_stopwords = {
        # 默认列表中的词
        "游戏", "这个", "真的", "没有", "一个", "就是", "什么", "不是", "但是", "可以", "感觉", "不能", "不会", "会",
        
        # 平台/通用 ("bug" 保留, 因为它有时是重要主题)
        "steam", "epic", "uplay", "dev", "player", "players", "devs",
        
        # 中文噪音词 (语气、拟声、缩写)
        "哈哈", "哈哈哈", "哈哈哈哈", "嘎嘎", "咕咕", "xswl", "666", "yyds",
        "个人", "觉得", "玩", "比较", "问题", "建议", "希望", "知道", "小时",
        "方面", "总体", "来说", "目前", "东西", "内容", "体验", "有点", "很多", "一些",
        "怎么", "那么", "所以", "如果", "还是", "因为", "而且", "还有", "以及", "一堆",
        "反正", "为什么", "一块", "这款", "u003d",
        
        # 常见英文噪音词 (Jieba经常会分出单个英文字母/单词)
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", 
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "an", "is", "it", "to", "the", "and", "of", "in", "on", "for", "with",
        "my", "you", "me", "he", "she", "we", "they", "get", "go", "so",
        "lol", "wtf", "omg", "gg", "nice", "good", "bad", "play", "game", "games",
    }
    stopwords.update(game_specific_stopwords)
    return list(stopwords)

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
    vectorizer_model = CountVectorizer(tokenizer=_jieba_tokenizer, stop_words=stopwords)

    # 3. 初始化 BERTopic (保持不变)
    topic_model = BERTopic(
        embedding_model=embedding_model,
        vectorizer_model=vectorizer_model,
        language="multilingual",
        min_topic_size=5,
        top_n_words=20,
        calculate_probabilities=False,
        verbose=True
    )

    # 4. 训练模型 (保持不变)
    try:
        topics, _ = topic_model.fit_transform(docs)
        representative_docs = topic_model.get_representative_docs()
    except Exception as e:
        print(f"❌ BERTopic 训练失败: {e}")
        return {}, []

    print("BERTopic 训练完成。正在提取主题和摘要...")

    topic_map = {}
    echarts_word_data = []
    topic_info = topic_model.get_topic_info()
    
    # --- 【核心修改】---
    # 统一使用 get_topic() 和“筛选法”，彻底替换 row.Name 逻辑
    
    for _, row in topic_info[topic_info.Topic != -1].iterrows():
        topic_id = int(row.Topic)
        
        # 1. 从源头获取词汇和分数
        all_words_scores = topic_model.get_topic(topic_id) 

        # 2. 如果主题无效（e.g., 只有停用词），则跳过
        if not all_words_scores:
            continue

        # --- a. 构建 topic_map (使用“筛选法”) ---
        
        # 3. 【您的方案】筛选关键词，确保不为空
        keywords = []
        for word, score in all_words_scores[:7]: # 取前7个
            if word and word.strip(): # 筛选掉 None, "" 和 " "
                keywords.append(word)
        
        # 4. 如果筛选后没有关键词，也跳过
        if not keywords:
            continue
            
        # 5. 拼接 (这种方法永远不会在开头产生顿号)
        keywords_str = "、".join(keywords)
        
        # 6. (摘要逻辑：使用 Top 3)
        summary = "暂无代表性评论。"
        summary_docs = []
        if topic_id in representative_docs:
            for doc in representative_docs[topic_id][:3]:
                cleaned_doc = _clean_text(doc)
                if len(cleaned_doc) > 60: 
                    cleaned_doc = cleaned_doc[:60] + "..."
                summary_docs.append(f'"{cleaned_doc}"') 
        if summary_docs:
            summary = " | ".join(summary_docs)
        
        # 7. 存入 topic_map
        topic_map[topic_id] = {
            "keywords": keywords_str,
            "summary": summary
        }

        # --- b. 构建 echarts_word_data (使用相同源) ---
        for word, score in all_words_scores:
            if word and word.strip(): # 确保词云也不含空词
                word_value = max(int(score * 1000), 1)
                echarts_word_data.append({
                    "name": word,
                    "value": word_value,
                    "topic_id": topic_id
                })

    print(f"BERTopic 分析完毕。找到 {len(topic_map)} 个有效主题。")
    return topic_map, echarts_word_data