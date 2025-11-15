import numpy as np
import pandas as pd

# 【新增】Steam 官方评级到基础分的映射
# 我们同时包含中英文，因为爬虫抓取的 summary 语言可能不固定
STEAM_RATING_MAP = {
    # --- 积极 ---
    "Overwhelmingly Positive": 98,
    "好评如潮": 98,
    "Very Positive": 88,
    "特别好评": 88,
    "Mostly Positive": 85,
    "多半好评": 85,
    "Positive": 82,
    "好评": 82,
    
    # --- 中立 ---
    "Mixed": 60,
    "褒贬不一": 60,
    
    # --- 消极 ---
    "Mostly Negative": 30,
    "多半差评": 30,
    "Negative": 10,
    "差评": 10,
    "Overwhelmingly Negative": 5,
    "差评如潮": 5,
    
    # --- 回退 ---
    "No user reviews": 50,
    "无评分": 50
}

# 关键词列表 (仅用于建议)
CRITICAL_FLAW_KEYWORDS = [
    "闪退", "崩溃", "bug", "服务器", "连接", 
    "优化", "掉帧", "欺诈", "打不开", "无法启动"
]

def calculate_recommend_score(df, game_info, topic_map, review_summary):
    """
    【V3.0 - 评级映射 + 减分模型】
    使用 Steam 官方评级字符串作为基础分，然后结合多维情感分析进行动态减分。
    
    :param df: 包含 *采样* 评论的 DataFrame (用于计算雷达均值)
    :param game_info: 游戏详情字典
    :param topic_map: BERTopic 分析出的主题字典 (用于关键词检查)
    :param review_summary: 包含 *真实* 评论总数和评级描述的字典
    :return: (recommend_score, suggestion)
    """
    
    if df.empty:
        return 50, "评论数据不足，评估中立。"

    # --- 1. 基础分 (100%) ---
    # 【核心修改】使用 Steam 官方评级字符串
    
    rating_string = review_summary.get('review_score_desc', '无评分')
    base_score = 50 # 默认中立
    
    # 使用 "in" 是为了匹配 "好评 (1,234)" 这样的字符串
    for key, score in STEAM_RATING_MAP.items():
        if key in rating_string:
            base_score = score
            break
    
    # --- 2. 核心减分项 (保持 V2.0 逻辑不变，最多 35 分) ---
    
    # A: “优化/联机” 减分 (最高 15 分)
    opt_penalty = 0
    if 'score_opt' in df.columns:
        opt_mean_score = df['score_opt'].mean()
        # 优化均分 0 -> 减 15 分
        opt_penalty = (1.0 - opt_mean_score) * 15
    
    # B: “性价比” 减分 (最高 10 分)
    value_penalty = 0
    if 'score_value' in df.columns:
        price_str = game_info.get('price', '0').replace('¥', '').replace(',', '').strip()
        if price_str.lower() not in ['free', '免费', '0'] and price_str:
            value_mean_score = df['score_value'].mean()
            value_penalty = (1.0 - value_mean_score) * 10
    
    # C: “退款率” 减分 (最高 10 分)
    refund_penalty = 0
    negative_reviews = df[df['voted_up'] == False]
    total_negative_sampled = len(negative_reviews)
    
    if total_negative_sampled > 0:
        try:
            playtime_col = pd.to_numeric(df['playtime_at_review'])
            refund_reviews = negative_reviews[pd.to_numeric(negative_reviews['playtime_at_review']) <= 120]
            refund_rate = len(refund_reviews) / total_negative_sampled # (0-1)
            refund_penalty = refund_rate * 10
        except Exception as e:
            print(f"⚠️ [Risk Model] 计算退款率失败: {e}")
            pass 
    
    # --- 3. 汇总计算 ---
    total_penalty = opt_penalty + value_penalty + refund_penalty
    
    # 推荐分 = 基础分 - 减分
    final_score = base_score - total_penalty
    
    # 归一化 (0-100)
    final_score = int(np.clip(final_score, 0, 100))

    # --- 4. 生成建议 (保持 V2.0 逻辑不变) ---
    suggestion = ""
    flaw_detected = False
    try:
        all_topic_text = " ".join([info['keywords'] + info['summary'] for info in topic_map.values()])
        if any(kw in all_topic_text for kw in CRITICAL_FLAW_KEYWORDS):
            flaw_detected = True
    except Exception:
        pass

    if final_score > 90:
        suggestion = "【必玩神作】(90-100分) 官方评级极高，且我们的分析未发现明显短板。"
    elif final_score > 75:
        suggestion = "【强烈推荐】(75-90分) 游戏总体优秀。官方评级高，核心体验良好。"
    elif final_score > 50:
        suggestion = "【褒贬不一】(50-75分) 游戏评价两极分化。官方评级尚可，但请注意减分项。"
    else:
        suggestion = "【不推荐】(25-50分) 踩雷风险较高。官方评级低，且存在明显短板。"
    
    if final_score < 25:
        suggestion = "【千万别买】(0-25分) 风险极高！"

    # 针对性建议
    if opt_penalty > 10 and final_score < 75:
        suggestion += " [注意：游戏“优化/联机”问题被普遍提及]"
    if value_penalty > 7 and final_score < 75:
        suggestion += " [注意：玩家普遍认为游戏“性价比”偏低]"
    if refund_penalty > 7 and final_score < 75:
        suggestion += " [注意：大量差评集中在2小时内（可能存在Bug或欺诈）]"
    if flaw_detected and final_score < 75:
        suggestion += " [注意：主题中检测到“闪退/崩溃”等硬伤关键词]"

    return final_score, suggestion