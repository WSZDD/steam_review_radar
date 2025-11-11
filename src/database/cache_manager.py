import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
# 导入你新的爬虫函数
from src.crawler.steam_api_crawler import fetch_game_reviews

# --- 配置 ---
DB_NAME = "steam_cache.db" 
CACHE_DURATION_HOURS = 6   
# REVIEWS_PER_TYPE = 50 # 你新的爬虫默认为50

def _init_db():
    """初始化数据库，创建元数据表（如果不存在）"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 确保表结构是最新的
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata (
        appid INTEGER PRIMARY KEY,
        last_updated TIMESTAMP,
        total_positive INTEGER,
        total_negative INTEGER
    )
    """)
    conn.commit()
    conn.close()

def _check_cache_validity(appid):
    """检查指定 appid 的缓存是否仍然有效"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT last_updated FROM metadata WHERE appid = ?", (appid,))
        result = cursor.fetchone()
        if result:
            last_updated = datetime.fromisoformat(result[0])
            if datetime.now() - last_updated < timedelta(hours=CACHE_DURATION_HOURS):
                return True
    except sqlite3.Error as e:
        print(f"❌ 检查缓存时出错: {e}")
        return False
    finally:
        conn.close()
    return False

def get_reviews_with_cache(appid, game_real_name, force_update=False):
    """
    核心函数：获取游戏评论，优先使用缓存。
    返回: (DataFrame, is_fresh_fetch: bool, summary: dict)
    """
    _init_db() 
    table_name = f"reviews_{appid}"
    
    # 1. 检查缓存是否有效
    if not force_update and _check_cache_validity(appid):
        print(f"✅ [Cache HIT] 缓存有效，从数据库加载 {game_real_name}")
        conn = sqlite3.connect(DB_NAME)
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            
            # --- 核心修复：从 metadata 读取 summary ---
            summary = {}
            cursor = conn.cursor()
            cursor.execute("SELECT total_positive, total_negative FROM metadata WHERE appid = ?", (appid,))
            summary_data = cursor.fetchone()
            if summary_data:
                summary = {'total_positive': summary_data[0], 'total_negative': summary_data[1]}
            # --- 修复结束 ---

            conn.close()
            if not df.empty:
                return df, False, summary # <-- 返回 3 个值
        except Exception as e:
            print(f"⚠️ 缓存读取失败 (table: {table_name})，将重新爬取... Error: {e}")
            
    # 2. [Cache MISS] 缓存无效或不存在，从 API 爬取
    print(f"❌ [Cache MISS] 缓存无效，将为 {game_real_name} 爬取好评和差评...")
    
    try:
        print(f"  ...正在爬取 [好评]...")
        # --- 核心修改：调用你新的爬虫函数 ---
        df_positive, summary = fetch_game_reviews(appid, review_type="positive", num_reviews=50) 
        
        print(f"  ...正在爬取 [差评]...")
        df_negative, _ = fetch_game_reviews(appid, review_type="negative", num_reviews=50)
    
    except Exception as e:
        print(f"❌ 爬虫 fetch_game_reviews 失败: {e}")
        return pd.DataFrame(), False, {} # 返回 3 个值

    df = pd.concat([df_positive, df_negative], ignore_index=True)
        
    if df.empty:
        print("爬取到空数据，不写入缓存。")
        return df, False, {} # 返回 3 个值

    # 3. [Cache WRITE] 写入新缓存
    conn = sqlite3.connect(DB_NAME)
    try:
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        cursor = conn.cursor()
        total_pos = summary.get('total_positive', 0)
        total_neg = summary.get('total_negative', 0)
        cursor.execute("""
            REPLACE INTO metadata (appid, last_updated, total_positive, total_negative) 
            VALUES (?, ?, ?, ?)
        """, (appid, datetime.now().isoformat(), total_pos, total_neg))
        
        conn.commit()
        print(f"💾 [Cache WRITE] 成功将 {len(df)} 条评论和摘要写入数据库。")
    except Exception as e:
        print(f"❌ 写入数据库失败: {e}")
    finally:
        conn.close()
        
    return df, True, summary # <-- 返回 3 个值