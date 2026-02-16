"""Data Analysis Agent 主程序入口"""

import os
import logging
from dotenv import load_dotenv

from src.analysis import DataAnalyzer
from src.ai import AIAnalyzer
from src.reporting import ReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数 - 示例使用流程"""

    # 加载环境变量
    load_dotenv()

    logger.info("启动Data Analysis Agent")

    # 初始化组件
    data_analyzer = DataAnalyzer()
    ai_analyzer = AIAnalyzer()
    report_generator = ReportGenerator()

    # 示例工作流
    print("\n" + "="*50)
    print("Data Analysis Agent - 智能数据分析系统")
    print("="*50 + "\n")

    print("功能模块:")
    print("1. 数据分析器 (DataAnalyzer) - 已初始化")
    print("2. AI分析器 (AIAnalyzer) - 已初始化")
    print("3. 报告生成器 (ReportGenerator) - 已初始化")

    print("\n使用示例:")
    print("""
# 1. 加载数据
analyzer = DataAnalyzer()
data = analyzer.load_data('data/your_data.csv')

# 2. 执行分析
results = analyzer.analyze()

# 3. 获取AI洞察
ai = AIAnalyzer()
insights = ai.analyze_data_insights(results)

# 4. 生成报告
reporter = ReportGenerator()
report_path = reporter.generate_markdown_report(results, insights)
    """)

    print("\n提示: 请将数据文件放入 data/ 目录，然后运行分析")
    print("详细文档请查看 README.md\n")


if __name__ == "__main__":
    main()
