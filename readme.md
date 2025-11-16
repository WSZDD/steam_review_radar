# 🎮 Steam 游戏评论雷达 (Steam Review Radar)

Steam 游戏评论雷达是一个 Web 应用程序，旨在帮助用户快速分析 Steam 平台上的游戏评论。用户只需输入游戏名称，应用即可抓取、分析并可视化呈现游戏的评论数据，帮助玩家从多个维度（如情感、主题、游玩时长）深入了解一款游戏。

## ✨ 主要功能

* **游戏信息检索**: 自动从 Steam API 获取游戏的基本信息，包括封面、价格、开发商和官方评分。
* **多维度情感分析**:
    * **情感雷达图**: 从多个预设维度（如图形、音效、玩法等）分析好评评论，生成直观的雷达图。
    * **时序分析**: 展示好评与差评随时间变化的趋势图，帮助识别口碑变化。
    * **玩家体验阶段**: 分析不同游玩时长（如新手、老玩家）的情感分布，了解游戏在不同阶段的玩家满意度。
* **AI 驱动的主题建模**:
    * 使用 **BERTopic** 自动从好评和差评中提取核心主题（如“闪退”、“优化差”、“剧情感人”）。
    * 为每个主题生成**AI摘要**，帮助用户快速理解玩家的主要反馈点。
    * **交互式词云**: 主题与词云图高亮联动，点击主题可查看相关的关键词。
* **智能推荐指数**: 综合多维度情感评分和 Steam 官方评分，计算出一个“游戏推荐指数”，为玩家提供购买建议。
* **动态前端体验**:
    * 所有图表均使用 **ECharts** 绘制，美观且可交互。
    * 卡片和图表**滚动懒加载**和**淡入淡出**动画，提升浏览体验。
* **数据缓存**: 使用 SQLite 缓存 Steam API 的请求结果和分析数据，提供“强制更新”选项，避免重复抓取，提高加载速度。

## 🛠️ 技术栈

| 类别 | 技术 |
| :--- | :--- |
| **后端** | Flask, Pandas |
| **前端** | Bootstrap 5, ECharts, jQuery |
| **数据分析** | BERTopic, scikit-learn, transformers (Hugging Face) |
| **数据爬取** | Requests |
| **数据库** | SQLite (用于缓存) |

## 🚀 部署与运行

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/WSZDD/steam_review_radar.git](https://github.com/WSZDD/steam_review_radar.git)
    cd steam_review_radar
    ```

2.  **创建虚拟环境并安装依赖**
    ```bash
    # (推荐) 创建虚拟环境
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

    # 安装所有依赖
    pip install -r requirements.txt
    ```

3.  **配置环境变量**
    创建`.env` 文件。你需要一个 **Steam Web API 密钥** 才能运行爬虫。
    STEAM_API_KEY=你的Steam Web API密钥

4.  **运行应用**
    ```bash
    python app.py
    ```
    应用将在 `http://127.0.0.1:5000` 启动。
