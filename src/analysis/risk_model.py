def compute_risk(sentiment_avg, price, dev_reputation, release_year):
    score = (
        (1 - sentiment_avg) * 0.5 +
        (price / 200) * 0.2 +
        (1 - dev_reputation) * 0.2 +
        ((2025 - release_year) / 10) * 0.1
    )
    return min(score, 1.0)
