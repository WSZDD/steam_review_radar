import requests
import pandas as pd
import time

import requests
import pandas as pd

def fetch_game_reviews(appid, language="schinese", num_reviews=50):
    """
    获取 Steam 游戏评论，返回 DataFrame 包含：
    author_name、author_avatar、content、voted_up
    """
    url = f"https://store.steampowered.com/appreviews/{appid}?json=1&language={language}&num_per_page={num_reviews}&purchase_type=all"
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
        "appid": appid  # 添加游戏 appid
    } for r in reviews])


    return df


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
