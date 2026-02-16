"""AI增强分析功能 - 使用Claude进行智能数据解读"""

import os
from typing import Dict, Any, Optional
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """AI分析器 - 使用Claude进行智能数据分析和洞察"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化AI分析器

        Args:
            api_key: Anthropic API密钥，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("未设置ANTHROPIC_API_KEY，AI功能将不可用")
            self.client = None
        else:
            self.client = Anthropic(api_key=self.api_key)

    def analyze_data_insights(self, data_summary: Dict[str, Any]) -> str:
        """
        基于数据摘要生成AI洞察

        Args:
            data_summary: 数据分析结果摘要

        Returns:
            AI生成的数据洞察和建议
        """
        if not self.client:
            return "AI功能未启用，请设置ANTHROPIC_API_KEY"

        prompt = self._build_analysis_prompt(data_summary)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return f"AI分析出错: {str(e)}"

    def _build_analysis_prompt(self, data_summary: Dict[str, Any]) -> str:
        """构建分析提示词"""
        prompt = f"""作为一个专业的数据分析师，请分析以下数据摘要并提供洞察：

数据概览：
- 数据形状: {data_summary.get('metadata', {}).get('shape', 'N/A')}
- 列名: {', '.join(data_summary.get('metadata', {}).get('columns', []))}

统计信息：
{self._format_statistics(data_summary.get('statistics', {}))}

异常值检测：
{data_summary.get('outliers', {})}

请提供：
1. 数据质量评估
2. 主要发现和趋势
3. 潜在的数据问题
4. 后续分析建议
5. 可视化建议

请用中文回答，并保持专业和简洁。"""

        return prompt

    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """格式化统计信息为可读文本"""
        if not stats:
            return "无统计信息"

        formatted = []

        # 缺失值信息
        missing = stats.get('missing_values', {})
        if missing:
            formatted.append(f"缺失值: {missing}")

        # 数据类型
        dtypes = stats.get('data_types', {})
        if dtypes:
            formatted.append(f"数据类型: {dtypes}")

        return '\n'.join(formatted)

    def suggest_visualizations(self, columns: list, dtypes: Dict[str, str]) -> list:
        """
        基于数据类型建议可视化方案

        Args:
            columns: 列名列表
            dtypes: 数据类型字典

        Returns:
            建议的可视化列表
        """
        suggestions = []

        numeric_cols = [col for col, dtype in dtypes.items()
                       if 'int' in dtype or 'float' in dtype]
        categorical_cols = [col for col, dtype in dtypes.items()
                          if 'object' in dtype or 'category' in dtype]

        if len(numeric_cols) >= 2:
            suggestions.append({
                'type': 'correlation_heatmap',
                'description': '数值列相关性热力图',
                'columns': numeric_cols
            })

        if numeric_cols:
            suggestions.append({
                'type': 'distribution',
                'description': '数值分布直方图',
                'columns': numeric_cols
            })

        if categorical_cols:
            suggestions.append({
                'type': 'bar_chart',
                'description': '分类变量柱状图',
                'columns': categorical_cols
            })

        if numeric_cols and categorical_cols:
            suggestions.append({
                'type': 'box_plot',
                'description': '按分类的数值分布箱线图',
                'numeric': numeric_cols,
                'categorical': categorical_cols
            })

        return suggestions
