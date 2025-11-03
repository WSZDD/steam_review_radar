import jieba.analyse

def extract_negative_keywords(reviews, sentiment_col='sentiment', content_col='content'):
    neg_texts = [r[content_col] for _, r in reviews.iterrows() if r[sentiment_col] < 0.4]
    text = " ".join(neg_texts)
    keywords = jieba.analyse.extract_tags(text, topK=30, withWeight=True)
    return keywords
