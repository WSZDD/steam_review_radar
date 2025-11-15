import os
import json
import pandas as pd
import numpy as np
# 导入需要调用的分析函数
from src.analysis.topic_modeler import analyze_with_bertopic
from src.analysis.risk_model import calculate_recommend_score
# 【加回】导入时序分析爬虫
from src.crawler.steam_api_crawler import fetch_data_for_timeseries 

# 定义缓存目录
ANALYSIS_CACHE_DIR = "static/analysis_cache"
os.makedirs(ANALYSIS_CACHE_DIR, exist_ok=True)

def _calculate_playtime_sentiment(df):
    """
    【保留】分析一：计算玩家体验阶段
    """
    print("  ... 正在分析 [玩家体验阶段]...")
    try:
        df['avg_sentiment'] = df[[
            'score_gameplay', 'score_visuals', 'score_story', 'score_opt', 'score_value'
        ]].mean(axis=1)
        bins = [-1, 120, 600, 1200, 999999] 
        labels = ['0-2h (初见)', '2-10h (中期)', '10-20h (深入)', '20h+ (老炮)']
        df['playtime_bin'] = pd.cut(pd.to_numeric(df['playtime_at_review']), bins=bins, labels=labels, right=True)
        grouped = df.groupby(['playtime_bin', 'voted_up'])['avg_sentiment'].mean().unstack(fill_value=0.5)
        grouped = grouped.rename(columns={True: 'positive', False: 'negative'})
        if 'positive' not in grouped: grouped['positive'] = 0.5
        if 'negative' not in grouped: grouped['negative'] = 0.5
        data = {
            'labels': labels,
            'positive_scores': [round(s * 100, 1) for s in grouped['positive']],
            'negative_scores': [round(s * 100, 1) for s in grouped['negative']]
        }
        return data
    except Exception as e:
        print(f"❌ [AnalysisManager] 玩家体验阶段分析失败: {e}")
        return {}


def get_analysis_results(appid, df, game_info, review_summary, is_fresh_fetch, review_type):
    """
    协调所有分析并使用文件缓存。
    """
    
    # --- 1. 定义所有缓存文件的路径 ---
    score_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_score.json")
    pos_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_pos_topics.json")
    neg_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_neg_topics.json")
    radar_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_radar.json")
    playtime_sentiment_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_playtime_sentiment.json")
    # 【加回】时序图缓存
    time_series_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_timeseries.json")
    
    # --- 2. 检查是否需要重新计算 ---
    files_to_check = [score_cache_file, pos_topics_cache_file, neg_topics_cache_file, 
                      radar_cache_file, playtime_sentiment_cache_file, 
                      time_series_cache_file] # <-- 【加回】
    
    if is_fresh_fetch or not all(os.path.exists(f) for f in files_to_check):
        
        print(f"♻️ [AnalysisManager] 缓存丢失或数据已更新。正在运行 *所有* 分析...")
        
        positive_reviews = df[df["voted_up"] == True]
        negative_reviews = df[df["voted_up"] == False]

        # A: 差评主题 (BERTopic)
        print("  ... 正在分析 [差评] 主题...")
        neg_topic_map, neg_word_data = analyze_with_bertopic(negative_reviews["content"])
        with open(neg_topics_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"topic_map": neg_topic_map, "word_data": neg_word_data}, f, ensure_ascii=False)
        
        # B: 好评主题 (BERTopic)
        print("  ... 正在分析 [好评] 主题...")
        pos_topic_map, pos_word_data = analyze_with_bertopic(positive_reviews["content"])
        with open(pos_topics_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"topic_map": pos_topic_map, "word_data": pos_word_data}, f, ensure_ascii=False)

        # C: 推荐分数
        print("  ... 正在计算 [推荐指数]...")
        current_topic_map = pos_topic_map if review_type == "positive" else neg_topic_map
        recommend_score, suggestion = calculate_recommend_score(df, game_info, current_topic_map, review_summary)
        with open(score_cache_file, 'w', encoding='utf-8') as f:
            json.dump({"score": recommend_score, "suggestion": suggestion}, f, ensure_ascii=False)

        # D: 雷达图
        print("  ... 正在计算 [情感雷达]...")
        # ( ... 雷达图计算逻辑 ... )
        radar_dimensions = {
            "score_gameplay": "玩法性", "score_visuals": "画面/音乐", "score_story": "剧情叙事",
            "score_opt": "优化/联机", "score_value": "性价比"
        }
        radar_values = []
        indicator_config = []
        if not positive_reviews.empty:
            for col, name in radar_dimensions.items():
                if col in positive_reviews.columns:
                    avg_score = positive_reviews[col].mean() * 100 
                    radar_values.append(round(avg_score, 1))
                else: radar_values.append(0)
                indicator_config.append({"name": name, "max": 100})
        else:
             for col, name in radar_dimensions.items():
                radar_values.append(0)
                indicator_config.append({"name": name, "max": 100})
        radar_data = {"indicator": indicator_config, "value": radar_values}
        with open(radar_cache_file, 'w', encoding='utf-8') as f:
            json.dump(radar_data, f, ensure_ascii=False)

        # E: 玩家体验阶段
        playtime_sentiment_data = _calculate_playtime_sentiment(df)
        with open(playtime_sentiment_cache_file, 'w', encoding='utf-8') as f:
            json.dump(playtime_sentiment_data, f, ensure_ascii=False)
            
        # F: 【加回】情感时序分析
        print("  ... 正在分析 [情感时序]...")
        try:
            time_series_data = fetch_data_for_timeseries(appid) 
            with open(time_series_cache_file, 'w', encoding='utf-8') as f:
                json.dump(time_series_data, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ [AnalysisManager] 情感时序分析失败: {e}")

        print("✅ [AnalysisManager] 所有分析完成并已缓存。")

    else:
        print(f"✅ [AnalysisManager] 正在从缓存文件加载所有分析结果...")

    # --- 4. 组装返回结果 ---
    results = {}
    try:
        # A: 加载分数
        with open(score_cache_file, 'r', encoding='utf-8') as f:
            score_data = json.load(f)
        results["recommend_score"] = score_data['score']
        results["suggestion"] = score_data['suggestion']
        
        # B: 加载当前视图的主题 (词云 + 列表)
        topic_cache_file = pos_topics_cache_file if review_type == "positive" else neg_topics_cache_file
        with open(topic_cache_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)
        results["word_data_json"] = json.dumps(topic_data['word_data'], ensure_ascii=False)
        results["topic_map_json"] = json.dumps(topic_data['topic_map'], ensure_ascii=False)
        results["current_topic_map"] = topic_data['topic_map']
        
        # C: 加载雷达图
        with open(radar_cache_file, 'r', encoding='utf-8') as f:
            results["radar_json"] = json.dumps(json.load(f), ensure_ascii=False)

        # D: 加载玩家体验阶段
        with open(playtime_sentiment_cache_file, 'r', encoding='utf-8') as f:
            results["playtime_sentiment_json"] = json.dumps(json.load(f), ensure_ascii=False)
            
        # E: 【加回】加载时序数据
        with open(time_series_cache_file, 'r', encoding='utf-8') as f:
            results["time_series_json"] = json.dumps(json.load(f), ensure_ascii=False)
            
    except Exception as e:
        print(f"❌ [AnalysisManager] 从缓存加载分析结果时失败: {e}")
        results = {
            "recommend_score": 50, "suggestion": "分析缓存读取失败。",
            "word_data_json": "[]", "topic_map_json": "{}",
            "current_topic_map": {}, 
            "radar_json": "{}",
            "playtime_sentiment_json": "{}",
            "time_series_json": "{}" # <-- 【加回】
        }

    return results