import os
from config import Config
import logging

temp_dir = os.path.abspath(Config.TEMP_DIR)
os.makedirs(temp_dir, exist_ok=True)
fig_path = os.path.join(temp_dir, f"output_2333333.svg")

# 确保图形输出目录存在
print(os.makedirs(os.path.dirname(fig_path), exist_ok=True))

# 处理路径中的反斜杠 - 规范化路径格式
fig_path_julia = fig_path.replace('\\', '/')
logging.info(f"图像将保存到路径: {fig_path} (Julia格式: {fig_path_julia})")