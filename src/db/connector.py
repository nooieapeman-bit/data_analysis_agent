"""数据库连接器 - 通过SSH隧道连接AWS RDS MySQL"""

import logging
import pandas as pd
import pymysql
from sshtunnel import SSHTunnelForwarder

from config.db_config import SSH_CONFIG, RDS_CONFIG, BRAND_DB_MAP

logger = logging.getLogger(__name__)


class DBConnector:
    """通过SSH隧道连接RDS MySQL，支持品牌切换和DataFrame查询"""

    def __init__(self, brand: str = 'osaio'):
        self.brand = brand
        self.database = BRAND_DB_MAP[brand]
        self._tunnel = None
        self._connection = None

    def connect(self):
        """建立SSH隧道和MySQL连接"""
        logger.info(f"正在连接 [{self.brand}] 数据库: {self.database}")

        # 建立SSH隧道（密码认证）
        self._tunnel = SSHTunnelForwarder(
            (SSH_CONFIG['ssh_host'], SSH_CONFIG['ssh_port']),
            ssh_username=SSH_CONFIG['ssh_user'],
            ssh_password=SSH_CONFIG['ssh_pass'],
            remote_bind_address=(RDS_CONFIG['rds_host'], RDS_CONFIG['rds_port']),
        )
        self._tunnel.start()
        logger.info(f"SSH隧道已建立，本地端口: {self._tunnel.local_bind_port}")

        # 通过隧道连接MySQL
        self._connection = pymysql.connect(
            host='127.0.0.1',
            port=self._tunnel.local_bind_port,
            user=RDS_CONFIG['rds_user'],
            password=RDS_CONFIG['rds_pass'],
            database=self.database,
            charset='utf8mb4',
        )
        logger.info(f"MySQL连接成功: {self.database}")
        return self

    def close(self):
        """关闭连接和隧道"""
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._tunnel:
            self._tunnel.stop()
            self._tunnel = None
        logger.info("连接已关闭")

    def query_df(self, sql: str, params=None) -> pd.DataFrame:
        """执行SQL查询，返回DataFrame"""
        if not self._connection:
            raise RuntimeError("未连接数据库，请先调用 connect()")
        return pd.read_sql(sql, self._connection, params=params)

    def switch_database(self, brand: str):
        """切换品牌数据库（复用同一SSH隧道）"""
        if brand not in BRAND_DB_MAP:
            raise ValueError(f"未知品牌: {brand}，可选: {list(BRAND_DB_MAP.keys())}")

        self.brand = brand
        self.database = BRAND_DB_MAP[brand]
        if self._connection:
            self._connection.select_db(self.database)
            logger.info(f"已切换到数据库: {self.database}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
