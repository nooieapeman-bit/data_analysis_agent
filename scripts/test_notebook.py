"""测试 notebook 是否能正常运行"""
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys
import os

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
notebook_path = os.path.join(project_root, 'notebooks', '03_order_analysis.ipynb')
notebook_dir = os.path.join(project_root, 'notebooks')

# 读取 notebook
with open(notebook_path) as f:
    nb = nbformat.read(f, as_version=4)

# 执行 notebook
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

try:
    print(f'开始执行 {notebook_path}...')
    ep.preprocess(nb, {'metadata': {'path': notebook_dir}})
    print('\n✅ Notebook 执行成功!')
except Exception as e:
    print(f'\n❌ Notebook 执行失败:')
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
