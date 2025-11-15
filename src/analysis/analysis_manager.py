import os
import json
import pandas as pd
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
    radar_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_radar.json")

    # --- 2. 检查是否需要重新计算 ---
    # （如果数据是新爬取的，或者任何一个缓存文件丢失了）
    if is_fresh_fetch or not all(os.path.exists(f) for f in [score_cache_file, pos_topics_cache_file, neg_topics_cache_file, time_series_cache_file, radar_cache_file]):
        
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

        # D: 好差评时序分析 (调用独立爬虫)
        print("  ... 正在分析 [好差评时序]...")
        try:
            time_series_data = fetch_data_for_timeseries(appid) 
            with open(time_series_cache_file, 'w', encoding='utf-8') as f:
                json.dump(time_series_data, f)
        except Exception as e:
            print(f"❌ [AnalysisManager] 好差评时序分析失败: {e}")
        
        print("  ... 正在计算 [情感雷达]...")
        radar_dimensions = {
            "score_gameplay": "玩法性",
            "score_visuals": "画面/音乐",
            "score_story": "剧情叙事",
            "score_opt": "优化/联机",
            "score_value": "性价比"
        }
        
        radar_values = []
        indicator_config = []
        
        # 计算所有评论在每个维度上的平均分
        if not positive_reviews.empty:
            for col, name in radar_dimensions.items():
                if col in positive_reviews.columns:
                    # 乘以 100 转换为百分制
                    avg_score = positive_reviews[col].mean() * 100
                    radar_values.append(round(avg_score, 1))
                else:
                    radar_values.append(0) # 列不存在
                indicator_config.append({"name": name, "max": 100})
        else:
            # 如果没有好评，返回一个全 0 的雷达图
            print("⚠️ [AnalysisManager] 雷达图计算：未找到好评，返回 0 值。")
            for col, name in radar_dimensions.items():
                radar_values.append(0)
                indicator_config.append({"name": name, "max": 100})
            
        radar_data = {
            "indicator": indicator_config,
            "value": radar_values
        }
        
        with open(radar_cache_file, 'w', encoding='utf-8') as f:
            json.dump(radar_data, f)


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
        
        # B: 加载当前切换所需的主题 (用于 ECharts 词云 *和* HTML 列表)
        print(f"  ... 正在为 [{review_type}] 视图加载主题...")
        topic_cache_file = pos_topics_cache_file if review_type == "positive" else neg_topics_cache_file
        with open(topic_cache_file, 'r', encoding='utf-8') as f:
            topic_data = json.load(f)
        
        results["word_data_json"] = json.dumps(topic_data['word_data'])
        results["topic_map_json"] = json.dumps(topic_data['topic_map'])
        
        # 【修复】使用这个键 (current_topic_map) 来动态显示 HTML 列表
        results["current_topic_map"] = topic_data['topic_map']
        
        # D: 加载时序数据
        with open(time_series_cache_file, 'r', encoding='utf-8') as f:
            results["time_series_json"] = json.dumps(json.load(f))

        # 加载雷达图数据
        with open(radar_cache_file, 'r', encoding='utf-8') as f:
            results["radar_json"] = json.dumps(json.load(f))

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