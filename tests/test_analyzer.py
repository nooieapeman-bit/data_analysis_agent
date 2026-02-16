"""数据分析器测试"""

import pytest
import pandas as pd
import numpy as np
from src.analysis import DataAnalyzer


@pytest.fixture
def sample_data():
    """创建测试数据"""
    return pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50],
        'C': ['a', 'b', 'c', 'd', 'e']
    })


def test_data_analyzer_init():
    """测试分析器初始化"""
    analyzer = DataAnalyzer()
    assert analyzer.data is None
    assert analyzer.metadata == {}


def test_collect_metadata(sample_data):
    """测试元数据收集"""
    analyzer = DataAnalyzer()
    analyzer.data = sample_data
    analyzer._collect_metadata()

    assert 'shape' in analyzer.metadata
    assert 'columns' in analyzer.metadata
    assert analyzer.metadata['shape'] == (5, 3)


def test_basic_statistics(sample_data):
    """测试基础统计"""
    analyzer = DataAnalyzer()
    analyzer.data = sample_data
    analyzer._collect_metadata()

    stats = analyzer.basic_statistics()

    assert 'numeric_summary' in stats
    assert 'categorical_summary' in stats
    assert 'missing_values' in stats
