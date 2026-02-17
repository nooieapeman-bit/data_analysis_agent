"""
从远程 MySQL 拉取 2025年后的订单相关数据，清洗后存入本地 SQLite。
运行方式: python scripts/sync_order_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import pandas as pd
from src.db.connector import DBConnector

START_TS = 1735689600  # 2025-01-01 00:00:00 UTC
SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'order_data.db')

def sync_brand(db, brand, sqlite_conn):
    """拉取单个品牌的订单相关数据"""
    brand_lower = 'osaio' if brand == 'OSAIO' else 'nooie'
    db.switch_database(brand_lower)

    # 1. order 表 (status=1, pay_time >= 2025)
    print(f"  [{brand}] 拉取 order...")
    df_order = db.query_df(f"""
        SELECT id as order_int_id, order_id, uid, subscribe_id, product_id,
               status as order_status, description, pay_time,
               amount, currency, transaction_fee, is_sub, pay_type
        FROM `order`
        WHERE status = 1 AND pay_time >= {START_TS}
    """)
    df_order['brand'] = brand
    print(f"    order: {len(df_order):,} rows")

    # 2. subscribe 表 (只取有关联的)
    print(f"  [{brand}] 拉取 subscribe...")
    sub_ids = df_order['subscribe_id'].dropna().unique()
    if len(sub_ids) > 0:
        # OSAIO 有 support_dev_num, cloud_type; Nooie 没有
        if brand == 'OSAIO':
            df_sub = db.query_df(f"""
                SELECT subscribe_id, uid as sub_uid, product_id as sub_product_id,
                       amount as sub_amount, currency as sub_currency,
                       cycles_unit, cycles_time, status as sub_status,
                       create_time as sub_create_time, cancel_time as sub_cancel_time,
                       support_dev_num, cloud_type
                FROM subscribe
                WHERE create_time >= {START_TS} OR subscribe_id IN (
                    SELECT DISTINCT subscribe_id FROM `order` WHERE status=1 AND pay_time >= {START_TS}
                )
            """)
        else:
            df_sub = db.query_df(f"""
                SELECT subscribe_id, '' as sub_uid, product_id as sub_product_id,
                       amount as sub_amount, currency as sub_currency,
                       cycles_unit, cycles_time, status as sub_status,
                       create_time as sub_create_time, cancel_time as sub_cancel_time,
                       0 as support_dev_num, 0 as cloud_type
                FROM subscribe
                WHERE create_time >= {START_TS} OR subscribe_id IN (
                    SELECT DISTINCT subscribe_id FROM `order` WHERE status=1 AND pay_time >= {START_TS}
                )
            """)
        df_sub['brand'] = brand
    else:
        df_sub = pd.DataFrame()
    print(f"    subscribe: {len(df_sub):,} rows")

    # 3. set_meal 表 (全量，通常很小)
    print(f"  [{brand}] 拉取 set_meal...")
    # 两个品牌共有字段
    df_meal = db.query_df("""
        SELECT code, name, time, file_time, price, saleprice, status,
               time_unit, currency, level
        FROM set_meal
    """)
    df_meal['brand'] = brand
    print(f"    set_meal: {len(df_meal):,} rows")

    # 4. order_amount_info (只取关联的)
    print(f"  [{brand}] 拉取 order_amount_info...")
    df_amount = db.query_df(f"""
        SELECT oai.order_int_id, oai.model_code, oai.amount_cny,
               oai.transaction_fee_cny, oai.exchange_rate
        FROM order_amount_info oai
        INNER JOIN `order` o ON oai.order_int_id = o.id
        WHERE o.status = 1 AND o.pay_time >= {START_TS}
    """)
    df_amount['brand'] = brand
    print(f"    order_amount_info: {len(df_amount):,} rows")

    # 5. cloud_info (只取关联的)
    print(f"  [{brand}] 拉取 cloud_info...")
    df_cloud = db.query_df(f"""
        SELECT ci.id as cloud_id, ci.uid as cloud_uid, ci.uuid as cloud_uuid,
               ci.order_id, ci.start_time as cloud_start_time,
               ci.end_time as cloud_end_time, ci.file_time,
               ci.status as cloud_status, ci.is_delete, ci.level
        FROM cloud_info ci
        INNER JOIN `order` o ON ci.order_id = o.order_id
        WHERE o.status = 1 AND o.pay_time >= {START_TS}
    """)
    df_cloud['brand'] = brand
    print(f"    cloud_info: {len(df_cloud):,} rows")

    # 6. 设备统计 (用于覆盖率计算)
    print(f"  [{brand}] 拉取 device 统计...")
    import time
    now_ts = int(time.time())
    thirty_days_ago_ms = (now_ts - 30 * 86400) * 1000
    df_device_stats = db.query_df(f"""
        SELECT
            COUNT(DISTINCT uuid) as total_devices,
            SUM(CASE WHEN mq_online = 1 OR p2p_online = 1 OR online_time > {thirty_days_ago_ms} THEN 1 ELSE 0 END) as active_devices_30d
        FROM device
        WHERE create_time >= {START_TS}
    """)
    df_device_stats['brand'] = brand

    # 活跃订阅设备数
    df_active_sub = db.query_df(f"""
        SELECT COUNT(DISTINCT ci.uuid) as devices_with_subscription
        FROM cloud_info ci
        WHERE ci.end_time > {now_ts}
          AND ci.uuid IS NOT NULL AND ci.uuid != ''
          AND ci.is_delete = 0
    """)
    df_device_stats['devices_with_subscription'] = df_active_sub['devices_with_subscription'].iloc[0]
    print(f"    device stats: total={df_device_stats['total_devices'].iloc[0]:,}, active={df_device_stats['active_devices_30d'].iloc[0]:,}")

    # 写入 SQLite
    df_order.to_sql('orders', sqlite_conn, if_exists='append', index=False)
    if len(df_sub) > 0:
        df_sub.to_sql('subscribe', sqlite_conn, if_exists='append', index=False)
    df_meal.to_sql('set_meal', sqlite_conn, if_exists='append', index=False)
    df_amount.to_sql('order_amount_info', sqlite_conn, if_exists='append', index=False)
    df_cloud.to_sql('cloud_info', sqlite_conn, if_exists='append', index=False)
    df_device_stats.to_sql('device_stats', sqlite_conn, if_exists='append', index=False)

    print(f"  [{brand}] 写入 SQLite 完成")


def main():
    # 清理旧数据
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)
        print(f"已删除旧数据库: {SQLITE_PATH}")

    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    sqlite_conn = sqlite3.connect(SQLITE_PATH)

    print(f"连接远程 MySQL...")
    db = DBConnector(brand='osaio')
    db.connect()

    try:
        for brand in ['OSAIO', 'Nooie']:
            print(f"\n{'='*50}")
            print(f"同步 {brand} 数据")
            print('='*50)
            sync_brand(db, brand, sqlite_conn)
    finally:
        db.close()
        print("\nMySQL 连接已关闭")

    # 创建索引加速查询
    print("\n创建索引...")
    cursor = sqlite_conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_brand ON orders(brand)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_uid ON orders(uid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_pay_time ON orders(pay_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_subscribe_id ON orders(subscribe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscribe_id ON subscribe(subscribe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cloud_order_id ON cloud_info(order_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_amount_order_id ON order_amount_info(order_int_id)")
    sqlite_conn.commit()

    # 验证
    print("\n=== 数据量验证 ===")
    for table in ['orders', 'subscribe', 'set_meal', 'order_amount_info', 'cloud_info', 'device_stats']:
        cnt = pd.read_sql(f"SELECT brand, COUNT(*) as cnt FROM {table} GROUP BY brand", sqlite_conn)
        print(f"  {table}:")
        for _, row in cnt.iterrows():
            print(f"    {row['brand']}: {row['cnt']:,}")

    sqlite_conn.close()
    file_size = os.path.getsize(SQLITE_PATH) / 1024 / 1024
    print(f"\nSQLite 数据库: {SQLITE_PATH}")
    print(f"文件大小: {file_size:.1f} MB")
    print("完成!")


if __name__ == '__main__':
    main()
