# 🎮 Steam 游戏评论情感分析 + 踩雷预警系统

## 项目简介
基于 Steam API 的玩家评论数据，使用 NLP 分析游戏好评/差评原因，
结合价格、开发商口碑等因素，生成「游戏踩雷风险指数」。

## 主要功能
- 自动爬取评论数据（含中文）
- NLP 情感分析（SnowNLP + VADER）
- 差评关键词提取与词云展示
- 游戏风险评分与购买建议

## 启动方法
```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
