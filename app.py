from flask import Flask, render_template, request
import os
from src.crawler.steam_api_crawler import fetch_game_reviews, get_appid_by_name
from wordcloud import WordCloud
import pandas as pd
import requests
from flask import jsonify
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("STEAM_API_KEY")

app = Flask(__name__)

def generate_wordcloud(df, column_name, output_path):
    text = " ".join(df[column_name].dropna().astype(str).tolist())
    font_path = "static/fonts/SimHei.ttf"
    wc = WordCloud(
        width=800,
        height=400,
        background_color="black",   # 深色背景匹配网站风格
        colormap="cool",            # 使用冷色调（蓝青色系）
        font_path=font_path
    ).generate(text)
    wc.to_file(output_path)
    return output_path



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        game_name = request.form["game_name"]
        review_type = request.form.get("review_type", "positive")

        appid, game_real_name, img_url, game_info = get_appid_by_name(game_name)
        if not appid:
            return render_template("index.html", error="未找到该游戏，请检查名称")

        df = fetch_game_reviews(appid)
        if df.empty:
            return render_template("index.html", error="未获取到评论数据", game_info=game_info)

        positive_reviews = df[df["voted_up"] == True]
        negative_reviews = df[df["voted_up"] == False]

        os.makedirs("static/img", exist_ok=True)
        pos_wc_path = generate_wordcloud(positive_reviews, "content", "static/img/pos_wordcloud.png")
        neg_wc_path = generate_wordcloud(negative_reviews, "content", "static/img/neg_wordcloud.png")

        show_reviews = positive_reviews if review_type == "positive" else negative_reviews
        show_wc_path = pos_wc_path if review_type == "positive" else neg_wc_path
        review_label = "好评" if review_type == "positive" else "差评"

        return render_template(
            "index.html",
            game_name=game_real_name,
            img_url=img_url,
            review_type=review_type,
            review_label=review_label,
            reviews=show_reviews,
            wordcloud_path=show_wc_path,
            game_info=game_info
        )

    return render_template("index.html")

# ===== 评论详情接口 =====
@app.route("/comment_detail/<steamid>/<appid>")
def comment_detail(steamid, appid):
    """返回评论者昵称和头像"""
    try:
        # 调用 Steam 用户信息接口
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
