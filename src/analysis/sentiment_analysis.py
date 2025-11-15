from transformers import pipeline
import torch
import re

# 文本清理函数 (保持不变)
def clean_review_text(text):
    text = str(text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = text.strip()
    return text

class SentimentAnalyzer:
    """
    使用 Zero-Shot Classification 构建多维情感雷达
    """
    def __init__(self):
        print("🤖 [SentimentAnalyzer] 正在加载 Zero-Shot Classification 模型...")
        # 使用支持中文的轻量级多语言 NLI 模型
        # 推荐: MoritzLaurer/mDeBERTa-v3-base-mnli-xnli (效果极佳且体积适中)
        # 备选: vicgalle/xlm-roberta-large-xnli-anli (更强但更慢)
        self.model_name = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
        
        try:
            device = 0 if torch.cuda.is_available() else -1
            
            self.classifier = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=device # 使用自动检测的设备
            )
            print("✅ [SentimentAnalyzer] 零样本模型加载成功。")
            if device == 0:
                print("✅ [SentimentAnalyzer] 已激活 CUDA (GPU) 加速！")
            else:
                print("⚠️ [SentimentAnalyzer] 未检测到 CUDA。正在使用 CPU（可能较慢）。")
        except Exception as e:
            print(f"❌ [SentimentAnalyzer] 模型加载失败: {e}")
            self.classifier = None

        # 定义雷达图的 5 个维度及其对应的“正向假设”
        # 模型会计算评论与这些句子的相似度(蕴含概率)
        self.dimension_map = {
            "score_gameplay": "玩法很有趣",
            "score_visuals":  "画面很精美",
            "score_story":    "剧情很感人",
            "score_opt":      "运行很流畅",  # 包含优化、服务器
            "score_value":    "价格很良心"   # 性价比
        }
        # 提取标签列表供模型使用
        self.labels = list(self.dimension_map.values())

    def analyze_batch(self, texts):
        """
        对一个 列表/Series 的文本进行批量情感分析。
        
        返回: 
        - 一个字典列表, e.g., [{'score_gameplay': 0.9, ...}, {...}]
        """
        # 定义回退的默认值
        default_scores = {k: 0.5 for k in self.dimension_map.keys()}
        
        if not self.classifier:
            return [default_scores for _ in texts]

        try:
            # 1. 批量清理和截断文本
            cleaned_texts = []
            for text in texts:
                cleaned = clean_review_text(text)[:512]
                # 如果清理后为空，给一个空格，防止模型出错
                cleaned_texts.append(cleaned if cleaned else " ") 

            print(f"🤖 [SentimentAnalyzer] 正在批量分析 {len(cleaned_texts)} 条评论...")
            
            # 2. 【核心】一次性运行所有文本
            # batch_size=8 是一个对 CPU/入门GPU 比较均衡的设置
            results_list = self.classifier(
                cleaned_texts, 
                self.labels, 
                multi_label=True, 
                batch_size=8 
            )
            
            print("✅ [SentimentAnalyzer] 批量分析完成。")

            # 3. 批量处理结果
            final_scores_list = []
            for result in results_list:
                # result 类似 {'labels': [...], 'scores': [...]}
                output_scores = {k: 0.0 for k in self.dimension_map.keys()} # 先用 0.0 填充
                for label, score in zip(result['labels'], result['scores']):
                    key = [k for k, v in self.dimension_map.items() if v == label][0]
                    output_scores[key] = score
                final_scores_list.append(output_scores)
            
            return final_scores_list

        except Exception as e:
            print(f"❌ [SentimentAnalyzer] 批量分析时出错: {e}")
            return [default_scores for _ in texts]