from snownlp import SnowNLP
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def sentiment_score(text):
    try:
        s = SnowNLP(text)
        return s.sentiments
    except:
        score = analyzer.polarity_scores(text)['compound']
        return (score + 1) / 2
