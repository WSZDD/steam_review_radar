from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

def generate_wordcloud(keywords):
    """
    生成词云并保存为图片
    """
    font_path = "static/fonts/SimHei.ttf"
    text = ' '.join([keyword[0] for keyword in keywords])  # 从关键词列表生成文本
    wordcloud = WordCloud(width=800, height=400, background_color="white", font_path=font_path).generate(text)

    # 保存图片到 static/img 目录
    img_path = "static/img/wordcloud.png"
    wordcloud.to_file(img_path)
    
    return img_path  # 返回生成图片的路径
