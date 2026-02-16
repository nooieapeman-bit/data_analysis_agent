"""数据库配置 - 从.env读取SSH隧道和RDS连接信息"""

import os
from dotenv import load_dotenv

load_dotenv()

# SSH隧道配置
SSH_CONFIG = {
    'ssh_host': os.getenv('SSH_HOST'),
    'ssh_port': int(os.getenv('SSH_PORT', 22)),
    'ssh_user': os.getenv('SSH_USER'),
    'ssh_pass': os.getenv('SSH_PASS'),
}

# RDS MySQL配置
RDS_CONFIG = {
    'rds_host': os.getenv('RDS_HOST'),
    'rds_port': int(os.getenv('RDS_PORT', 3306)),
    'rds_user': os.getenv('RDS_USER'),
    'rds_pass': os.getenv('RDS_PASS'),
}

# 品牌 → 数据库映射
BRAND_DB_MAP = {
    'osaio': 'bi_center',
    'nooie': 'nooie_bi_center',
}

# 分析目标表
TARGET_TABLES = ['user', 'user_device', '`order`', 'subscribe']
