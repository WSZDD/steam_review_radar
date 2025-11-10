from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from src.preprocess.text_cleaner import clean_text
from snownlp import SnowNLP
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
def load_stopwords(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # 使用 set 结构以便快速查找
            return {line.strip() for line in f}
    except FileNotFoundError:
        print(f"警告: 停用词文件未找到: {filepath}。词云可能包含无意义的词。")
        return set()

def generate_wordcloud(df, column_name, output_path):
    STOPWORDS = load_stopwords(os.path.join(BASE_DIR, '..', '..', 'static', 'cn_stopwords.txt'))
    # 1. 【新增】一个列表来存储所有有意义的词
    meaningful_words = []
    
    print(f"\n--- 开始为 {output_path} 提取关键词 ---")
    
    # 2. 【修改】逐条处理评论
    # 使用 .dropna().astype(str) 确保数据是干净的字符串
    for review in df[column_name].dropna().astype(str):
        # 3. (不变) 清洗文本
        cleaned_review = clean_text(review) # 使用你的清洗函数
        if not cleaned_review:
            continue

        # 4. 【新增】使用 SnowNLP 进行词性标注
        try:
            s = SnowNLP(cleaned_review)
            tags = s.tags
        except Exception as e:
            # print(f"SnowNLP 处理出错: {e} - 跳过: {cleaned_review[:20]}")
            continue # SnowNLP 可能对某些特殊输入（如纯表情或太短）出错

        # 5. 【新增】提取名词和形容词
        for word, tag in tags:
            word = word.strip()
            # 核心过滤逻辑:
            # 1. 是名词 (tag 以 'n' 开头) 或 形容词 (tag 以 'a' 开头)
            # 2. 词的长度 > 1 (过滤单字)
            # 3. 这个词不在我们的停用词表 (STOPWORDS) 中
            if (tag.startswith('n') or tag.startswith('a')) and len(word) > 1 and word not in STOPWORDS:
                meaningful_words.append(word)

    # 6. 【修改】将所有提取到的“原因词”组合成一个长字符串
    text = " ".join(meaningful_words)
    
    # 8. (不变) 检查分词后是否为空
    font_path = "static/fonts/SIMHEI.TTF"   
    
    if not text.strip():
        return None
    
    # 9. (不变) 生成词云
    wc = WordCloud(
        width=800,
        height=400,
        background_color="black",   
        colormap="cool",            
        font_path=font_path
    ).generate(text)
    
    wc.to_file(output_path)
    return output_path
