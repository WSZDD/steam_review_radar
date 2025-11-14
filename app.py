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
# --- 核心修改：导入新的分析管理器 ---
from src.analysis.analysis_manager import get_analysis_results

load_dotenv()
API_KEY = os.getenv("STEAM_API_KEY")

app = Flask(__name__)

# --- 缓存目录和时序爬虫已移走 ---

@app.route("/", methods=["GET", "POST"])
def index():
    # --- 默认值 ---
    game_name_search_term = ""
    review_type = "positive"
    game_info = None
    reviews = pd.DataFrame()
    positive_count = 0
    negative_count = 0
    review_label = "评论"
    error = None
    
    # 分析结果的默认值
    analysis_results = {
        "recommend_score": None, "suggestion": None,
        "word_data_json": "[]", "topic_map_json": "{}",
        "negative_topics": {}, "time_series_json": "{}",
        "scatter_json": "{}"
    }

    if request.method == "POST":
        game_name_search_term = request.form["game_name"]
        review_type = request.form.get("review_type", "positive")
        force_update = "force_update_button" in request.form
        
        appid, game_real_name, img_url, game_info = get_appid_by_name(game_name_search_term)
        
        if not appid:
            error = "未找到该游戏，请检查名称"
        else:
            # 1. 从数据库缓存获取评论
            df, is_fresh_fetch, review_summary = get_reviews_with_cache(
                appid, game_real_name, force_update=force_update
            )

            if df.empty:
                error = "未获取到评论数据"
            else:
                # 2. 准备基础数据
                positive_reviews = df[df["voted_up"] == True]
                negative_reviews = df[df["voted_up"] == False]
                positive_count = len(positive_reviews)
                negative_count = len(negative_reviews)
                review_label = "好评" if review_type == "positive" else "差评"
                reviews_to_analyze = positive_reviews if review_type == "positive" else negative_reviews
                reviews = reviews_to_analyze # 用于 Masonry 布局
                
                # --- 3. 【核心修改】调用分析管理器 ---
                analysis_results = get_analysis_results(
                    appid, df, game_info, review_summary, 
                    is_fresh_fetch, review_type
                )
                # --- 修改结束 ---

    # --- 4. 统一 render_template ---
    return render_template(
        "index.html",
        game_info=game_info,
        game_name=game_name_search_term,
        review_type=review_type,
        review_label=review_label,
        reviews=reviews,
        positive_count=positive_count,
        negative_count=negative_count,
        error=error,
        
        # --- 使用字典解包传递所有分析结果 ---
        **analysis_results
    )

# ===== 评论详情接口 (不变) =====
@app.route("/comment_detail/<steamid>/<appid>")
def comment_detail(steamid, appid):
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
    app.run(debug=True, use_reloader=False)