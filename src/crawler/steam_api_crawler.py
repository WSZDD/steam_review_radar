import requests
import pandas as pd
from src.analysis.sentiment_analysis import SentimentAnalyzer
try:
    analyzer = SentimentAnalyzer()
except Exception as e:
    print(f"CRITICAL: 无法初始化 SentimentAnalyzer. {e}")
    analyzer = None

def fetch_game_reviews(appid, language="schinese", num_reviews=50, review_type="all"):
    """
    获取 Steam 游戏评论，返回 DataFrame 包含：
    author_name、author_avatar、content、voted_up
    """
    url = (
        f"https://store.steampowered.com/appreviews/{appid}"
        f"?json=1"
        f"&language={language}"
        f"&filter=all"                     # ✅ 按“有帮助度”排序
        f"&review_type={review_type}"
        f"&day_range=9223372036854775807"  # ✅ 全时间范围
        f"&num_per_page={num_reviews}"
        f"&cursor=*"
    )
    params_summary = (
        f"https://store.steampowered.com/appreviews/{appid}"
        f"?json=1"
        f"&language=all"
        f"&review_type=all"
        f"&num_per_page=0"
        f"&cursor=*"
    )
    print(url)
    res = requests.get(url)
    data = res.json()
    reviews = data.get("reviews", [])

    # 检查是否获取到评论
    if not reviews:
        return pd.DataFrame(columns=["author_name", "author_avatar", "content", "voted_up"])

    df = pd.DataFrame([{
        "author_name": r["author"].get("steamid", "匿名"),
        "author_avatar": r["author"].get("avatar", ""),  # 小头像URL
        "content": r.get("review", ""),
        "voted_up": r.get("voted_up", False),
        "appid": appid,  # 添加游戏 appid
        "playtime_at_review": r["author"].get("playtime_at_review", 0),
        "votes_up": r.get("votes_up", 0)
    } for r in reviews])

    if analyzer:
        print("🤖 [Crawler] 正在对爬取内容进行情感分析...")
        # 定义一个辅助函数
        def analyze_row(content):
            score, label = analyzer.analyze(content)
            return pd.Series([score, label])
        
        # 使用 .apply 一次性获取两列
        df[['sentiment_score', 'sentiment_label']] = df['content'].apply(analyze_row)
        print("✅ [Crawler] 情感分析完成。")
    else:
        print("⚠️ [Crawler] 情感分析器未初始化，跳过分析。")
        df['sentiment_score'] = 0.5
        df['sentiment_label'] = 'neutral'

    res_summary = requests.get(params_summary)
    res_summary.raise_for_status()
    summary_data = res_summary.json()
    
    summary = {} # 默认为空
    if summary_data and summary_data.get("success") == 1:
        # 这个 summary 将包含 total_positive 和 total_negative
        summary = summary_data.get("query_summary", {})

    return df, summary


def get_appid_by_name(game_name):
    """
    根据游戏名从 Steam 搜索接口获取 appid、真实游戏名、封面图、游戏详情
    """
    search_url = "https://store.steampowered.com/api/storesearch"
    params = {"term": game_name, "l": "schinese", "cc": "CN"}
    res = requests.get(search_url, params=params)

    data = res.json()

    if not data.get("items"):
        return None, None, None, None

    game = data["items"][0]
    appid = game["id"]
    game_real_name = game["name"]
    img_url = game["tiny_image"]

    # ====== 获取游戏详细信息 ======
    detail_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=schinese&cc=CN"
    detail_res = requests.get(detail_url).json()
    detail = detail_res[str(appid)]["data"]

    info = {
        "name": detail.get("name"),
        "release_date": detail.get("release_date", {}).get("date", "未知"),
        "price": detail.get("price_overview", {}).get("final_formatted", "免费") if detail.get("is_free") == False else "免费",
        "developer": ", ".join(detail.get("developers", [])) if detail.get("developers") else "未知",
        "publisher": ", ".join(detail.get("publishers", [])) if detail.get("publishers") else "未知",
        "short_description": detail.get("short_description", "暂无简介"),
        "header_image": detail.get("header_image", img_url),
    }

    return appid, game_real_name, img_url, info
