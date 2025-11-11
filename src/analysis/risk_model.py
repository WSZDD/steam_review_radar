import numpy as np
import pandas as pd

# 定义“硬伤”关键词列表
CRITICAL_FLAW_KEYWORDS = [
    "闪退", "崩溃", "bug", "服务器", "连接", 
    "优化", "掉帧", "欺诈", "打不开", "无法启动"
]

def calculate_recommend_score(df, game_info, topic_map, review_summary):
    """
    计算多维度「游戏推荐指数」(0-100)，分数越高越推荐。
    
    :param df: 包含 *采样* 评论的 DataFrame
    :param game_info: 游戏详情字典
    :param topic_map: BERTopic 分析出的主题字典
    :param review_summary: 包含 *真实* 评论总数的字典
    :return: (recommend_score, suggestion)
    """
    
    if df.empty:
        return 50, "评论数据不足，评估中立。"

    # --- 1. 基础风险 (权重 30%) ---
    # (这部分不变，计算的是“风险”)
    base_risk = 0
    total_pos = review_summary.get('total_positive', 0)
    total_neg = review_summary.get('total_negative', 0)
    total_all = total_pos + total_neg

    if total_all > 0:
        negative_rate = total_neg / total_all
        base_risk = negative_rate * 30
    else:
        print("⚠️ [Risk Model] 未能从 review_summary 获取好评/差评数。")

    # --- 2. 核心风险 (权重 50%) ---
    # (这部分不变，计算的是“风险”)
    negative_reviews = df[df['voted_up'] == False]
    total_negative_sampled = len(negative_reviews)

    if total_negative_sampled == 0:
        # 基础风险很低（几乎没差评），直接给高分
        return 95, "好评如潮！几乎没有差评，可以放心入手。"

    # 特征 A: “退款指标” (25%)
    refund_risk = 0
    try:
        df['playtime_at_review'] = pd.to_numeric(df['playtime_at_review'])
        refund_reviews = negative_reviews[negative_reviews['playtime_at_review'] <= 120]
        refund_rate = len(refund_reviews) / total_negative_sampled 
        refund_risk = refund_rate * 25
    except KeyError:
        print("⚠️ [Risk Model] 未找到 'playtime_at_review' 列，跳过“退款指标”。")

    # 特征 B: “差评含金量” (25%)
    helpfulness_risk = 0
    try:
        df['votes_up'] = pd.to_numeric(df['votes_up'])
        avg_helpfulness = negative_reviews['votes_up'].mean()
        helpfulness_score = np.clip(avg_helpfulness / 20.0, 0, 1)
        helpfulness_risk = helpfulness_score * 25
    except KeyError:
        print("⚠️ [Risk Model] 未找到 'votes_up' 列，跳过“差评含金量”。")
    
    core_risk = refund_risk + helpfulness_risk

    # --- 3. 调整项 (权重 20%) ---
    # (这部分不变，计算的是“风险”)
    flaw_risk = 0
    try:
        all_topic_text = " ".join([info['keywords'] + info['summary'] for info in topic_map.values()])
        if any(kw in all_topic_text for kw in CRITICAL_FLAW_KEYWORDS):
            flaw_risk = 10 
    except Exception:
        pass # 忽略错误

    price_risk = 0
    try:
        price_str = game_info.get('price', '0').replace('¥', '').replace(',', '').strip()
        if price_str.lower() not in ['free', '免费', '0'] and price_str:
            price_float = float(price_str)
            if price_float > 200: 
                price_risk = 10
            elif price_float > 100:
                price_risk = 5
    except Exception:
        pass # 忽略错误

    adjustment_risk = flaw_risk + price_risk
    
    # --- 4. 汇总计算 ---
    final_risk_score = int(base_risk + core_risk + adjustment_risk)
    final_risk_score = max(0, min(100, final_risk_score)) # 这是“风险”

    # --- 5. 【核心修改】反转分数 ---
    recommend_score = 100 - final_risk_score # 这是“推荐分”

    # --- 6. 生成新建议 (基于推荐分) ---
    if recommend_score > 90:
        suggestion = "【必玩神作】(90-100分) 好评如潮，几乎没有缺点，可以放心入手！"
    elif recommend_score > 75:
        suggestion = "【强烈推荐】(75-90分) 游戏总体优秀。差评多为个人喜好或小问题，值得购买。"
    elif recommend_score > 50:
        suggestion = "【褒贬不一】(50-75分) 游戏评价两极分化。优点突出，但差评反映的问题（如Bug、优化）值得高度关注。"
    elif recommend_score > 25:
        suggestion = "【不推荐】(25-50分) 踩雷风险较高。差评普遍反映了“硬伤”或“退款级”体验，建议谨慎观望。"
    else:
        suggestion = "【千万别买】(0-25分) 风险极高！评论区反映出严重问题，强烈不推荐。"

    return recommend_score, suggestion