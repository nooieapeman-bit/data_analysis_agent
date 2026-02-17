"""
从 MySQL 拉取每个 subscribe_id 的全局首次付费时间（含2025年前历史）
用于判断订单是首期还是续费
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from src.db.connector import DBConnector

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'order_data.db')

def sync_brand(db, brand, sqlite_conn):
    """拉取单个品牌的 subscribe 首次付费时间"""
    brand_lower = 'osaio' if brand == 'OSAIO' else 'nooie'
    db.switch_database(brand_lower)

    print(f"\n  [{brand}] 查询全局首次付费时间...")

    # 获取所有 subscribe_id 的最早 pay_time（不限时间范围）
    df_first_pay = db.query_df("""
        SELECT
            subscribe_id,
            MIN(pay_time) as first_pay_time
        FROM `order`
        WHERE status = 1 AND amount > 0 AND subscribe_id IS NOT NULL AND subscribe_id != ''
        GROUP BY subscribe_id
    """)

    df_first_pay['brand'] = brand
    print(f"    {brand}: {len(df_first_pay):,} subscribe_id")

    # 统计有多少是2025年之前首次付费的
    ts_2025 = 1735689600  # 2025-01-01 00:00:00 UTC
    pre_2025_count = (df_first_pay['first_pay_time'] < ts_2025).sum()
    print(f"    其中 {pre_2025_count:,} ({pre_2025_count/len(df_first_pay)*100:.1f}%) 在2025年前首次付费")

    return df_first_pay

def main():
    print("连接 SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)

    # 删除旧表（如果存在）
    cursor = sqlite_conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS subscribe_first_pay")
    sqlite_conn.commit()
    print("已清理旧 subscribe_first_pay 表")

    print("\n连接远程 MySQL...")
    db = DBConnector(brand='osaio')
    db.connect()

    all_data = []

    try:
        for brand in ['OSAIO', 'Nooie']:
            print(f"\n{'='*50}")
            print(f"同步 {brand}")
            print('='*50)
            df = sync_brand(db, brand, sqlite_conn)
            all_data.append(df)
    finally:
        db.close()
        print("\nMySQL 连接已关闭")

    # 合并并写入 SQLite
    print("\n写入 SQLite...")
    df_all = pd.concat(all_data, ignore_index=True)
    df_all.to_sql('subscribe_first_pay', sqlite_conn, if_exists='replace', index=False)

    # 创建索引
    print("创建索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_first_pay_subscribe_id ON subscribe_first_pay(subscribe_id, brand)")
    sqlite_conn.commit()

    # 验证
    print("\n=== 数据验证 ===")
    verify = pd.read_sql("SELECT brand, COUNT(*) as cnt FROM subscribe_first_pay GROUP BY brand", sqlite_conn)
    print(verify)

    sqlite_conn.close()
    print("\n完成!")

if __name__ == '__main__':
    main()
