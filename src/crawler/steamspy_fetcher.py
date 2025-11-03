"""
获取 SteamSpy 元数据（价格、评分、发行商、发布时间）
API: https://steamspy.com/api.php?request=appdetails&appid=<id>
"""
import requests

def fetch_game_metadata(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else {}
