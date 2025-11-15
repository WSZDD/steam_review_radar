import requests
import pandas as pd
import numpy as np
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
    print(f"🕷️ [Crawler] Fetching: {url}")
    res = requests.get(url)
    data = res.json()
    reviews = data.get("reviews", [])

    if not reviews:
        # 返回包含新列的空 DataFrame
        cols = ["author_name", "author_avatar", "content", "voted_up", 
                "score_gameplay", "score_visuals", "score_story", "score_opt", "score_value"]
        return pd.DataFrame(columns=cols), {}

    # 1. 构造基础 DataFrame
    df = pd.DataFrame([{
        "author_name": r["author"].get("steamid", "匿名"),
        "author_avatar": r["author"].get("avatar", ""),
        "content": r.get("review", ""),
        "voted_up": r.get("voted_up", False),
        "appid": appid,
        "playtime_at_review": r["author"].get("playtime_at_review", 0),
        "votes_up": r.get("votes_up", 0),
        "timestamp_created": r.get("timestamp_created", 0)
    } for r in reviews])

    # 2. 执行多维情感分析
    if analyzer:
        print(f"🤖 [Crawler] 正在对 {len(df)} 条评论进行多维雷达分析...")
        
        score_dicts = analyzer.analyze_batch(df['content'])
        
        # 转换为 DataFrame 并合并
        df_scores = pd.DataFrame(score_dicts)
        df = pd.concat([df, df_scores], axis=1)
        
        print("✅ [Crawler] 多维分析完成。")
    else:
        # 填充默认值
        for col in ["score_gameplay", "score_visuals", "score_story", "score_opt", "score_value"]:
            df[col] = 0.5

    # ... (Summary 获取部分保持不变) ...
    res_summary = requests.get(params_summary)
    summary = {}
    if res_summary.status_code == 200:
        summary_data = res_summary.json()
        if summary_data.get("success") == 1:
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

# --- 【核心修改】替换这个函数 ---
def fetch_data_for_timeseries(appid, max_pages=10):
    """
    专门为时序分析爬取大量（最多 1000 条）评论。
    【已修改】按月统计好评数和差评数。
    """
    print(f"🔬 [TimeSeries] 开始为 {appid} 爬取时序数据 (最多 {max_pages} 页)...")
    all_reviews_data = []
    next_cursor = "*" 
    
    for page in range(max_pages):
        if not next_cursor:
            break 
        
        print(f"  ... 正在爬取时序数据第 {page+1}/{max_pages} 页")
        
        params = {
            "json": 1,
            "language": "all", 
            "filter": "all",  # 按“有帮助”排序，获取全时间跨度
            "day_range": "9223372036854775807",
            "num_per_page": 1000,
            "cursor": next_cursor 
        }
        
        try:
            res = requests.get(f"https://store.steampowered.com/appreviews/{appid}", params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            if data.get("success") != 1 or "reviews" not in data:
                break
                
            for review in data["reviews"]:
                # --- 【修改】不再需要情感分析 ---
                all_reviews_data.append({
                    "timestamp_created": review.get("timestamp_created", 0),
                    "voted_up": review.get("voted_up", False) # 只需要好评/差评
                })
            
            next_cursor = data.get("cursor") 
            
        except Exception as e:
            print(f"❌ [TimeSeries] 爬取分页时出错: {e}")
            break
    
    print(f"✅ [TimeSeries] 爬取完毕，共 {len(all_reviews_data)} 条评论。")
    
    if not all_reviews_data:
        return {} # 返回空字典

    # --- 【核心修改】使用 Pandas 进行高级分组统计 ---
    df_time = pd.DataFrame(all_reviews_data)
    df_time['timestamp'] = pd.to_datetime(df_time['timestamp_created'], unit='s')
    df_time = df_time.set_index('timestamp')

    # 1. 按 'voted_up' (True/False) 分组
    # 2. 按月 ('M') 重采样
    # 3. 统计每组的数量 (.size())
    # 4. 将 'voted_up' (True/False) 作为列展开 (.unstack())
    counts_over_time = df_time.groupby('voted_up').resample('M').size().unstack(level=0, fill_value=0)
    
    # 5. 重命名列
    counts_over_time = counts_over_time.rename(columns={True: 'positive', False: 'negative'})
    
    # 6. 确保两列都存在
    if 'positive' not in counts_over_time:
        counts_over_time['positive'] = 0
    if 'negative' not in counts_over_time:
        counts_over_time['negative'] = 0

    # 7. 排序
    counts_over_time = counts_over_time.sort_index()

    # 8. 格式化为 ECharts 需要的数据结构
    time_series_data = {
        'dates': [date.strftime('%Y-%m') for date in counts_over_time.index],
        'positive_counts': counts_over_time['positive'].tolist(),
        'negative_counts': counts_over_time['negative'].tolist()
    }
    return time_series_data
# --- 【替换结束】 ---