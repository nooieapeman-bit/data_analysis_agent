"""核心数据分析器"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器主类"""

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[str, Any] = {}

    def load_data(self, filepath: str, **kwargs) -> pd.DataFrame:
        """
        加载数据文件

        Args:
            filepath: 数据文件路径
            **kwargs: pandas读取参数

        Returns:
            加载的DataFrame
        """
        try:
            if filepath.endswith('.csv'):
                self.data = pd.read_csv(filepath, **kwargs)
            elif filepath.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(filepath, **kwargs)
            elif filepath.endswith('.json'):
                self.data = pd.read_json(filepath, **kwargs)
            else:
                raise ValueError(f"不支持的文件格式: {filepath}")

            logger.info(f"成功加载数据: {filepath}, 形状: {self.data.shape}")
            self._collect_metadata()
            return self.data

        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            raise

    def load_from_db(self, connector, sql: str, params=None) -> pd.DataFrame:
        """
        从数据库加载数据

        Args:
            connector: DBConnector实例（需已连接）
            sql: SQL查询语句
            params: SQL参数

        Returns:
            加载的DataFrame
        """
        try:
            self.data = connector.query_df(sql, params=params)
            logger.info(f"从数据库加载数据成功, 形状: {self.data.shape}")
            self._collect_metadata()
            return self.data
        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
            raise

    def _collect_metadata(self):
        """收集数据元信息"""
        if self.data is not None:
            self.metadata = {
                'shape': self.data.shape,
                'columns': list(self.data.columns),
                'dtypes': self.data.dtypes.to_dict(),
                'missing_values': self.data.isnull().sum().to_dict(),
                'memory_usage': self.data.memory_usage(deep=True).sum()
            }

    def basic_statistics(self) -> Dict[str, Any]:
        """
        计算基础统计信息

        Returns:
            包含各类统计指标的字典
        """
        if self.data is None:
            raise ValueError("请先加载数据")

        stats = {
            'numeric_summary': self.data.describe().to_dict(),
            'categorical_summary': {},
            'missing_values': self.data.isnull().sum().to_dict(),
            'data_types': self.data.dtypes.astype(str).to_dict()
        }

        # 分类变量统计
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            stats['categorical_summary'][col] = {
                'unique_count': self.data[col].nunique(),
                'top_values': self.data[col].value_counts().head(5).to_dict()
            }

        return stats

    def clean_data(self, strategy: str = 'drop', fill_value=None) -> pd.DataFrame:
        """
        数据清洗

        Args:
            strategy: 处理缺失值的策略 ('drop', 'fill', 'forward_fill', 'backward_fill')
            fill_value: 填充值（当strategy='fill'时使用）

        Returns:
            清洗后的DataFrame
        """
        if self.data is None:
            raise ValueError("请先加载数据")

        cleaned_data = self.data.copy()

        if strategy == 'drop':
            cleaned_data = cleaned_data.dropna()
        elif strategy == 'fill':
            cleaned_data = cleaned_data.fillna(fill_value)
        elif strategy == 'forward_fill':
            cleaned_data = cleaned_data.fillna(method='ffill')
        elif strategy == 'backward_fill':
            cleaned_data = cleaned_data.fillna(method='bfill')
        else:
            raise ValueError(f"未知的策略: {strategy}")

        logger.info(f"数据清洗完成: {self.data.shape} -> {cleaned_data.shape}")
        self.data = cleaned_data
        return cleaned_data

    def analyze(self) -> Dict[str, Any]:
        """
        执行完整的数据分析

        Returns:
            分析结果字典
        """
        if self.data is None:
            raise ValueError("请先加载数据")

        results = {
            'metadata': self.metadata,
            'statistics': self.basic_statistics(),
            'correlations': self._calculate_correlations(),
            'outliers': self._detect_outliers()
        }

        return results

    def _calculate_correlations(self) -> Dict[str, Any]:
        """计算数值列之间的相关性"""
        numeric_data = self.data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            return {}
        return numeric_data.corr().to_dict()

    def _detect_outliers(self, method: str = 'iqr') -> Dict[str, Any]:
        """检测异常值"""
        outliers = {}
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if method == 'iqr':
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_count = ((self.data[col] < lower_bound) |
                               (self.data[col] > upper_bound)).sum()
                outliers[col] = int(outlier_count)

        return outliers
