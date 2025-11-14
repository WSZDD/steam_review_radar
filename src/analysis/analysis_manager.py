import os
import json
import pandas as pd
import numpy as np
# 导入需要调用的分析函数
from src.analysis.topic_modeler import analyze_with_bertopic
from src.analysis.risk_model import calculate_recommend_score
from src.crawler.steam_api_crawler import fetch_data_for_timeseries # 导入我们刚移动的函数

# 定义缓存目录
ANALYSIS_CACHE_DIR = "static/analysis_cache"
os.makedirs(ANALYSIS_CACHE_DIR, exist_ok=True)

def get_analysis_results(appid, df, game_info, review_summary, is_fresh_fetch, review_type):
    """
    协调所有分析（BERTopic, Risk, TimeSeries）并使用文件缓存。
    返回一个包含所有前端所需数据的字典。
    """
    
    # --- 1. 定义所有缓存文件的路径 ---
    score_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_score.json")
    pos_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_pos_topics.json")
    neg_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_neg_topics.json")
    time_series_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_timeseries.json")
    scatter_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_scatter.json")

    # --- 2. 检查是否需要重新计算 ---
    # （如果数据是新爬取的，或者任何一个缓存文件丢失了）
    if is_fresh_fetch or not all(os.path.exists(f) for f in [score_cache_file, pos_topics_cache_file, neg_topics_cache_file, time_series_cache_file, scatter_cache_file]):
        
        print(f"♻️ [AnalysisManager] 缓存丢失或数据已更新。正在运行 *所有* 分析...")
        
        # 分离好评/差评 (用于 BERTopic)
        positive_reviews = df[df["voted_up"] == True]
        negative_reviews = df[df["voted_up"] == False]

        # A: 分析差评主题 (BERTopic)
        print("  ... 正在分析 [差评] 主题...")
        neg_topic_map, neg_word_data = analyze_with_bertopic(negative_reviews["content"])
        with open(neg_topics_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"topic_map": neg_topic_map, "word_data": neg_word_data}, f)
        
        # B: 分析好评主题 (BERTopic)
        print("  ... 正在分析 [好评] 主题...")
        pos_topic_map, pos_word_data = analyze_with_bertopic(positive_reviews["content"])
        with open(pos_topics_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"topic_map": pos_topic_map, "word_data": pos_word_data}, f)

        # C: 计算推荐分数 (依赖 差评主题)
        print("  ... 正在计算 [推荐指数]...")
        recommend_score, suggestion = calculate_recommend_score(df, game_info, neg_topic_map, review_summary)
        with open(score_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"score": recommend_score, "suggestion": suggestion}, f)

        # D: 情感时序分析 (调用独立爬虫)
        print("  ... 正在分析 [情感时序]...")
        try:
            time_series_data = fetch_data_for_timeseries(appid) 
            with open(time_series_cache_file, 'w', encoding='utf-8') as f:
                json.dump(time_series_data, f)
        except Exception as e:
            print(f"❌ [AnalysisManager] 情感时序分析失败: {e}")
        
        print("  ... 正在分析 [时长与情感]...")
        try:
            scatter_data = {'positive': [], 'negative': []}
            # (df 是包含所有评论的完整 DataFrame)
            
            # 我们最多只绘制 500 个点，防止浏览器卡顿
            df_sample = df.sample(n=min(len(df), 500)) 
            
            for _, row in df_sample.iterrows():
                # 将分钟转为小时
                playtime_hours = row['playtime_at_review'] / 60.0
                
                # 使用对数转换 (log(x+1)) 来压缩 X 轴
                log_playtime = np.log1p(playtime_hours) 
                
                score = row['sentiment_score']
                
                # data 格式: [x轴, y轴, 附加信息(用于tooltip)]
                point_data = [log_playtime, score, round(playtime_hours, 1)] 
                
                if row['voted_up']:
                    scatter_data['positive'].append(point_data)
                else:
                    scatter_data['negative'].append(point_data)
            
            # 存入缓存
            with open(scatter_cache_file, 'w', encoding='utf-8') as f:
                json.dump(scatter_data, f)
        except Exception as e:
            print(f"❌ [AnalysisManager] 散点图分析失败: {e}")

        print("✅ [AnalysisManager] 所有分析完成并已缓存。")

    else:
        # 3. 如果不需要重新计算，则从文件加载
        print(f"✅ [AnalysisManager] 正在从缓存文件加载所有分析结果...")

    # --- 4. 组装返回结果 ---
    results = {}
    try:
        # A: 加载分数
        with open(score_cache_file, 'r', encoding='utf-8') as f:
            score_data = json.load(f)
        results["recommend_score"] = score_data['score']
        results["suggestion"] = score_data['suggestion']
        
        # B: 加载当前切换所需的主题 (用于 ECharts 词云)
        print(f"  ... 正在为 [{review_type}] 视图加载主题...")
        topic_cache_file = pos_topics_cache_file if review_type == "positive" else neg_topics_cache_file
        with open(topic_cache_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)
        results["word_data_json"] = json.dumps(topic_data['word_data'])
        results["topic_map_json"] = json.dumps(topic_data['topic_map'])

        # C: 加载 *差评* 主题 (用于 HTML 列表)
        with open(neg_topics_cache_file, 'r', encoding='utf-8') as f:
            results["negative_topics"] = json.load(f)['topic_map']
        
        # D: 加载时序数据
        with open(time_series_cache_file, 'r', encoding='utf-8') as f:
            results["time_series_json"] = json.dumps(json.load(f))

        # --- E: 加载散点图数据 ---
        with open(scatter_cache_file, 'r', encoding='utf-8') as f:
            # 同样转换为 JSON 字符串
            results["scatter_json"] = json.dumps(json.load(f))

    except Exception as e:
        print(f"❌ [AnalysisManager] 从缓存加载分析结果时失败: {e}")
        # 返回空值，防止前端崩溃
        results = {
            "recommend_score": 50, "suggestion": "分析缓存读取失败。",
            "word_data_json": "[]", "topic_map_json": "{}",
            "negative_topics": {}, "time_series_json": "{}",
            "scatter_json": "{}"
        }

    return results