import os
import platform
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 检测当前操作系统
    IS_WINDOWS = platform.system() == "Windows"
    
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Julia 可执行文件路径 - 根据操作系统选择适当路径
    if IS_WINDOWS:
        JULIA_PATH = os.getenv("JULIA_PATH", r"C:\Users\Public\TongYuan\julia-1.9.3\bin\julia.exe")
    else:
        JULIA_PATH = os.getenv("JULIA_PATH", "/app/Syslab-2025/Tools/julia-1.9.3/bin/julia")

    # 日志路径 - 根据操作系统选择适当路径
    if IS_WINDOWS:
        LOG_PATH = os.getenv("LOG_PATH", r"C:\Users\Public\TongYuan\logs")
    else:
        LOG_PATH = os.getenv("LOG_PATH", "/app/Syslab-2025/logs")
    
    # 临时文件目录 (使用绝对路径)
    TEMP_DIR = os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp"))
    
    # 执行超时时间（秒）
    EXEC_TIMEOUT = int(os.getenv("EXEC_TIMEOUT", 120))
    
    # 环境变量 - 根据操作系统设置
    if IS_WINDOWS:
        ENV = {
            "PYTHON": "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe",
            "JULIA_DEPOT_PATH": "C:/Users/Public/TongYuan/.julia",
            "PATH": (
                "C:/Users/Public/TongYuan/.julia/miniforge3;"
                "C:/Users/Public/TongYuan/.julia/miniforge3/Scripts;"
                f"{os.environ['PATH']}"
            )
        }
    else:
        # Linux环境配置
        ENV = {
            "PYTHON": "/app/Syslab-2025/.julia/miniforge3/bin/python",
            "JULIA_DEPOT_PATH": "/app/Syslab-2025/.julia",
            "PATH": (
                "/app/Syslab-2025/.julia/miniforge3:"
                "/app/Syslab-2025/.julia/miniforge3/bin:"
                f"{os.environ['PATH']}"
            )
        }