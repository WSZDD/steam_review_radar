from flask import Flask, render_template, request
import os
import pandas as pd
import requests
from flask import jsonify
from dotenv import load_dotenv
import json

# --- 导入项目模块 ---
from src.crawler.steam_api_crawler import get_appid_by_name
from src.database.cache_manager import get_reviews_with_cache
from src.analysis.topic_modeler import analyze_with_bertopic
from src.analysis.risk_model import calculate_recommend_score

load_dotenv()
API_KEY = os.getenv("STEAM_API_KEY")

app = Flask(__name__)

# --- 【新增】分析缓存配置 ---
ANALYSIS_CACHE_DIR = "static/analysis_cache"
os.makedirs(ANALYSIS_CACHE_DIR, exist_ok=True)
# --- 新增结束 ---

@app.route("/", methods=["GET", "POST"])
def index():
    # --- 默认值 ---
    game_name_search_term = ""
    review_type = "positive"
    game_info = None
    reviews = pd.DataFrame()
    word_data_json = "[]"
    topic_map_json = "{}"
    negative_topics = {}
    positive_count = 0
    negative_count = 0
    recommend_score = None
    suggestion = None
    error = None
    review_label = "评论"

    if request.method == "POST":
        game_name_search_term = request.form["game_name"]
        review_type = request.form.get("review_type", "positive")
        force_update = "force_update_button" in request.form
        
        appid, game_real_name, img_url, game_info = get_appid_by_name(game_name_search_term)
        
        if not appid:
            error = "未找到该游戏，请检查名称"
        else:
            df, is_fresh_fetch, review_summary = get_reviews_with_cache(
                appid, 
                game_real_name, 
                force_update=force_update
            )

            if df.empty:
                error = "未获取到评论数据"
            else:
                positive_reviews = df[df["voted_up"] == True]
                negative_reviews = df[df["voted_up"] == False]
                positive_count = len(positive_reviews)
                negative_count = len(negative_reviews)
                review_label = "好评" if review_type == "positive" else "差评"
                reviews_to_analyze = positive_reviews if review_type == "positive" else negative_reviews
                reviews = reviews_to_analyze # 用于 Masonry 布局

                # --- 【核心修改】分析缓存逻辑 ---
                
                # 定义缓存文件路径
                score_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_score.json")
                pos_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_pos_topics.json")
                neg_topics_cache_file = os.path.join(ANALYSIS_CACHE_DIR, f"{appid}_neg_topics.json")

                # 1. 检查是否需要重新计算
                if is_fresh_fetch or not os.path.exists(score_cache_file):
                    print(f"♻️ [Analysis] 缓存丢失或数据已更新。正在运行 *所有* 分析...")

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
                    
                    print("✅ [Analysis] 所有分析完成并已缓存。")

                else:
                    # 2. 如果不需要重新计算，则从文件加载
                    print(f"✅ [Analysis] 正在从缓存文件加载分析结果...")
                    
                    # A: 加载分数
                    with open(score_cache_file, 'r', encoding='utf-8') as f:
                        score_data = json.load(f)
                    recommend_score = score_data['score']
                    suggestion = score_data['suggestion']
                
                # 3. 加载 *当前切换* 所需的主题 (用于 ECharts 词云)
                print(f"  ... 正在为 [{review_label}] 视图加载主题...")
                if review_type == "positive":
                    with open(pos_topics_cache_file, 'r', encoding='utf-8') as f:
                        topic_data = json.load(f)
                else: # negative
                    with open(neg_topics_cache_file, 'r', encoding='utf-8') as f:
                        topic_data = json.load(f)
                
                topic_map_for_cloud = topic_data['topic_map']
                echarts_word_data = topic_data['word_data']
                word_data_json = json.dumps(echarts_word_data)
                topic_map_json = json.dumps(topic_map_for_cloud)

                # 4. 加载 *差评* 主题 (用于 HTML 列表)
                # (你的 index.html 模板中 `negative_topics` 是硬编码的)
                with open(neg_topics_cache_file, 'r', encoding='utf-8') as f:
                    negative_topics = json.load(f)['topic_map']
                
                # --- 【修改结束】 ---

    # --- 统一 render_template ---
    return render_template(
        "index.html",
        game_info=game_info,
        game_name=game_name_search_term,
        review_type=review_type,
        review_label=review_label,
        reviews=reviews,
        word_data_json=word_data_json,
        topic_map_json=topic_map_json,
        negative_topics=negative_topics, # 传给 HTML 列表
        positive_count=positive_count,
        negative_count=negative_count,
        recommend_score=recommend_score,
        suggestion=suggestion,
        error=error
    )

# ===== 评论详情接口 (不变) =====
@app.route("/comment_detail/<steamid>/<appid>")
def comment_detail(steamid, appid):
    """返回评论者昵称和头像"""
    try:
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={API_KEY}&steamids={steamid}"
        res = requests.get(url)
        data = res.json()["response"]["players"][0]
        return jsonify({
            "nickname": data.get("personaname", "匿名用户"),
            "avatar": data.get("avatarfull", "/static/default_avatar.png")
        })
    except Exception as e:
        print("❌ 获取评论者信息失败:", e)
        return jsonify({
            "nickname": "未知用户",
            "avatar": "/static/default_avatar.png"
        })

if __name__ == "__main__":
    app.run(debug=True)