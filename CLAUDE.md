# EU区数据分析项目 - 数据结构文档

## 项目概述

分析OSAIO和Nooie两个智能家居品牌在EU区的用户、设备、订单和订阅数据。

**数据库配置:**
- OSAIO数据库: `bi_center`
- Nooie数据库: `nooie_bi_center`
- 连接方式: SSH隧道 → AWS RDS MySQL
- 分析时间范围: 2025-01-01 至今

---

## 核心数据表结构

### 1. user 表 - 用户信息

**用途**: 存储注册用户的基本信息

**关键字段:**
```sql
uid              VARCHAR(20)   -- 用户唯一ID (主键)
register_time    INT           -- 注册时间 (Unix timestamp 秒)
register_country VARCHAR(10)   -- 注册国家 (电话区号, 如 44=UK, 49=Germany)
country_iso      VARCHAR(10)   -- ISO国家代码 (大多为空)
schema           VARCHAR(32)   -- AppID (3dab98eee85b7ae8=OSAIO, 4adcd2139621b1ef=NOOIE)
delete_time      INT           -- 删除时间 (Unix timestamp)
status           TINYINT       -- 用户状态
```

**业务规则:**
- `register_country` 是电话区号，不是ISO代码
- 用户来源分为两类:
  - **设备主人** (bind_type=1): 购买设备后通过说明书注册
  - **被分享用户** (bind_type=2): 设备主人分享设备给其他用户
- 用户状态删除(delete)不代表真实流失，很多用户不删除账号但永久不登录

**关键KPI:**
- **7天绑定成功率**: (注册后7天内绑定设备的用户数 - 被分享用户) / (总用户 - 被分享用户)
  - 计算时需排除最近7天注册的用户（未满7天观察期）
  - 被分享用户默认100%绑定成功，不计入分母

**2025年数据量:**
- OSAIO: 194,054 用户
- Nooie: 58,974 用户

---

### 2. device 表 - 设备信息

**用途**: 存储设备本身的信息（设备实体）

**关键字段:**
```sql
uuid         VARCHAR(32)  -- 设备唯一ID (主键)
device_id    VARCHAR(32)  -- 设备ID
model_code   VARCHAR(32)  -- 设备型号 (如 GP5_T6S8A3, IPC007_T6S6A3)
mq_online    TINYINT(1)   -- MQ连接在线状态 (0=离线, 1=在线)
p2p_online   TINYINT(1)   -- P2P连接在线状态 (0=离线, 1=在线)
online_time  BIGINT       -- 最近一次在线时间 (Unix timestamp 毫秒)
offline_time BIGINT       -- 最近一次离线时间 (Unix timestamp 毫秒)
create_time  INT          -- 设备创建时间 (Unix timestamp 秒)
wifi_level   TINYINT      -- WiFi信号强度 (dBm, 如 -52)
battery_online TINYINT(1) -- 是否为电池设备 (0=插电, 1=电池)
battery_level  INT        -- 电池电量百分比 (0-100)
```

**业务规则:**
- 设备在线状态: `mq_online=1 OR p2p_online=1` 即为在线
- **设备废弃定义**: 30天以上未在线的设备视为已废弃，不会再恢复使用
- `online_time` 和 `offline_time` 是**毫秒**时间戳，`create_time` 是**秒**时间戳

**关键KPI:**
- **设备废弃率**: 每月新增设备中，目前已超过30天未在线的占比
- **设备在线率**: 当前在线设备数 / 总设备数

**2025年数据量:**
- OSAIO: 197,166 设备 (在线率 55.3%, 废弃率 29.2%)
- Nooie: 30,965 设备 (在线率 44.1%, 废弃率 35.5%)

---

### 3. user_device 表 - 用户设备关系表

**用途**: 记录用户与设备的绑定关系（一个设备可以被多个用户绑定）

**关键字段:**
```sql
id           INT          -- 自增主键
uid          VARCHAR(20)  -- 用户ID (外键 → user.uid)
device_id    VARCHAR(32)  -- 设备ID (关联 device 表)
uuid         VARCHAR(32)  -- 设备UUID
model_code   VARCHAR(32)  -- 设备型号
bind_type    TINYINT(1)   -- 绑定类型 (1=设备主人/自购, 2=被分享)
status       TINYINT(1)   -- 绑定状态 (1=已绑定, 2=已解绑)
first_time   INT          -- 第一次绑定时间 (Unix timestamp 秒)
bind_time    INT          -- 最近一次绑定时间 (Unix timestamp 秒)
delete_time  INT          -- 解绑时间 (Unix timestamp 秒)
create_at    TIMESTAMP    -- 记录创建时间
```

**业务规则:**
- **bind_type=1**: 设备主人（通过设备说明书首次绑定）
- **bind_type=2**: 被分享用户（由设备主人通过APP分享）
- `first_time` = 第一次绑定时间（用于判断用户来源）
- `bind_time` = **最近一次**绑定时间（不是首次）
- `status=2` 且 `delete_time > 0` = 已解绑

**用户来源判定逻辑:**
```sql
-- 获取每个用户的第一台设备的 bind_type
SELECT t.uid, t.bind_type as first_bind_type FROM (
    SELECT ud.uid, ud.bind_type,
           ROW_NUMBER() OVER (PARTITION BY ud.uid ORDER BY ud.first_time ASC) as rn
    FROM user_device ud
    WHERE ud.first_time > 0
) t WHERE t.rn = 1
```
- 按 `first_time` 升序排序，取第一台设备
- 如果 `first_bind_type=1` → 设备主人
- 如果 `first_bind_type=2` → 被分享用户

**注意事项:**
- 不要单独分析 user_device 表，它是关系表
- 用户来源分析已在 user 表分析中完成
- 设备绑定/解绑数据已在分析中使用

**2025年绑定关系数据量:**
- OSAIO: ~280K 绑定关系
- Nooie: ~61K 绑定关系

---

## 数据表关系图

```
┌─────────────────┐
│  user (用户)    │
│  - uid (PK)     │
│  - register_time│
│  - register_    │
│    country      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐      N:1    ┌──────────────────┐
│  user_device    │◄──────────── │  device (设备)   │
│  (关系表)       │              │  - uuid (PK)     │
│  - uid (FK)     │              │  - model_code    │
│  - device_id    │              │  - online_time   │
│  - bind_type    │              │  - create_time   │
│  - first_time   │              └──────────────────┘
│  - status       │
└─────────────────┘
```

**关系说明:**
- 一个用户可以绑定多个设备 (1:N)
- 一个设备可以被多个用户绑定 (N:1)
- user_device 是中间关系表，记录绑定关系

---

## 时间字段统一说明

| 字段名 | 表 | 单位 | 示例值 | 转换方式 |
|--------|-----|------|--------|----------|
| register_time | user | **秒** | 1735689600 | `pd.to_datetime(df['register_time'], unit='s')` |
| create_time | device | **秒** | 1735689600 | `pd.to_datetime(df['create_time'], unit='s')` |
| first_time | user_device | **秒** | 1735689600 | `pd.to_datetime(df['first_time'], unit='s')` |
| bind_time | user_device | **秒** | 1735689600 | `pd.to_datetime(df['bind_time'], unit='s')` |
| delete_time | user_device | **秒** | 1735689600 | `pd.to_datetime(df['delete_time'], unit='s')` |
| online_time | device | **毫秒** | 1735689600000 | `pd.to_datetime(df['online_time'], unit='ms')` |
| offline_time | device | **毫秒** | 1735689600000 | `pd.to_datetime(df['offline_time'], unit='ms')` |

**注意**: device表的 online_time/offline_time 是毫秒，其他表的时间字段都是秒！

---

## 国家代码映射 (register_country)

user表的 `register_country` 字段存储的是**电话区号**，常见映射：

| 区号 | 国家 | 区号 | 国家 |
|------|------|------|------|
| 44 | UK | 49 | Germany |
| 33 | France | 34 | Spain |
| 39 | Italy | 31 | Netherlands |
| 43 | Austria | 48 | Poland |
| 351 | Portugal | 46 | Sweden |
| 1 | US/Canada | 86 | China |

完整映射代码见 `notebooks/01_user_analysis.ipynb` 的 COUNTRY_MAP 字典。

---

## AppID (schema) 映射

user表的 `schema` 字段表示用户所属的APP:

| schema值 | 品牌 |
|----------|------|
| 3dab98eee85b7ae8 | OSAIO |
| 4adcd2139621b1ef | NOOIE |
| e95fb28bdf38b904 | Victure |
| d67d982e1094c8af | Teckin |

**注意**: 本次分析聚焦 OSAIO 和 Nooie 两个品牌。

---

## 已完成的分析

### 1. 用户分析 (`01_user_analysis.ipynb`)

**分析维度:**
- 用户注册趋势（按日/周/月）
- 用户来源分析（自购设备 vs 被分享）
- 7天绑定成功率（核心KPI）
- 注册国家/地区分布
- 用户增长率（日均量）

**核心发现:**
- OSAIO 7天绑定成功率: 79.31%
- Nooie 7天绑定成功率: 58.22%
- OSAIO分享率: 17.16%, Nooie分享率: 26.18%

### 2. 设备分析 (`02_device_analysis.ipynb`)

**分析维度:**
- 设备创建趋势
- 设备型号分布
- 设备在线状态
- **设备健康度 - 30天+废弃率（核心KPI）**

**核心发现:**
- OSAIO在线率: 55.3%, 废弃率: 29.2%
- Nooie在线率: 44.1%, 废弃率: 35.5%
- OSAIO设备健康度优于Nooie

---

## 待完成的分析

### 3. 订单分析 (`order` 表)
- 待探索表结构

### 4. 订阅分析 (`subscribe` 表)
- 待探索表结构

---

## 开发注意事项

1. **时间戳单位**: device表的online_time/offline_time是毫秒，其他都是秒
2. **保留字**: MySQL中 `order` 是保留字，查询时需用反引号 `` `order` ``
3. **用户来源**: 必须用 `first_time` 排序取第一台设备的 bind_type，不能用 bind_time
4. **废弃设备**: 30天+未在线定义为废弃，计算公式 `(now - online_date).days > 30`
5. **当前月处理**: 月度统计时，当前不完整月需使用日均量 (total / elapsed_days)
6. **国家代码**: register_country 是电话区号，需映射到国家名称

---

## 数据质量说明

1. **country_iso 字段**: 大多为空，不可用于国家分析
2. **delete_time**: user表的删除时间不代表真实流失
3. **never online**: 部分设备从未上线过（online_time=0）
4. **电池设备**: 占比极少（OSAIO 0.3%, Nooie 0%）

---

最后更新: 2026-02-16
