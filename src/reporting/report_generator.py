"""自动化报告生成器"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器 - 自动生成分析报告"""

    def __init__(self, output_dir: str = './reports'):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_markdown_report(
        self,
        analysis_results: Dict[str, Any],
        ai_insights: Optional[str] = None,
        title: str = "数据分析报告"
    ) -> str:
        """
        生成Markdown格式报告

        Args:
            analysis_results: 分析结果
            ai_insights: AI生成的洞察
            title: 报告标题

        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        report_content = self._build_markdown_content(
            title, analysis_results, ai_insights
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"报告已生成: {filepath}")
        return filepath

    def _build_markdown_content(
        self,
        title: str,
        results: Dict[str, Any],
        ai_insights: Optional[str]
    ) -> str:
        """构建Markdown报告内容"""

        content = f"""# {title}

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 1. 数据概览

"""

        # 元数据
        metadata = results.get('metadata', {})
        if metadata:
            content += f"""
### 基本信息

- **数据形状**: {metadata.get('shape', 'N/A')}
- **列数**: {len(metadata.get('columns', []))}
- **内存占用**: {metadata.get('memory_usage', 0) / 1024 / 1024:.2f} MB

### 列信息

"""
            for col in metadata.get('columns', []):
                dtype = metadata.get('dtypes', {}).get(col, 'unknown')
                missing = metadata.get('missing_values', {}).get(col, 0)
                content += f"- **{col}**: {dtype} (缺失值: {missing})\n"

        # 统计信息
        content += "\n## 2. 统计分析\n\n"
        stats = results.get('statistics', {})

        if stats.get('missing_values'):
            content += "### 缺失值统计\n\n"
            for col, count in stats['missing_values'].items():
                if count > 0:
                    content += f"- {col}: {count}\n"

        # 异常值
        outliers = results.get('outliers', {})
        if outliers:
            content += "\n### 异常值检测\n\n"
            for col, count in outliers.items():
                if count > 0:
                    content += f"- {col}: {count} 个异常值\n"

        # AI洞察
        if ai_insights:
            content += f"\n## 3. AI智能洞察\n\n{ai_insights}\n"

        # 结论
        content += """
---

## 总结

本报告由Data Analysis Agent自动生成。
"""

        return content

    def generate_json_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        生成JSON格式报告

        Args:
            analysis_results: 分析结果

        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        report_data = {
            'generated_at': datetime.now().isoformat(),
            'results': analysis_results
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON报告已生成: {filepath}")
        return filepath
