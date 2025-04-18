import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Julia 可执行文件路径
    JULIA_PATH = os.getenv("JULIA_PATH", r"C:\Users\Public\TongYuan\julia-1.9.3\bin\julia.exe")

    # 日志路径
    LOG_PATH = os.getenv("LOG_PATH", r"C:\Users\Public\TongYuan\logs")
    
    # 临时文件目录 (使用绝对路径)
    TEMP_DIR = os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp"))
    
    # # 执行超时时间（秒）
    # EXEC_TIMEOUT = int(os.getenv("EXEC_TIMEOUT", 120))
    
    # 环境变量
    ENV = {
        "PYTHON": "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe",
        "JULIA_DEPOT_PATH": "C:/Users/Public/TongYuan/.julia",
        "PATH": (
            "C:/Users/Public/TongYuan/.julia/miniforge3;"
            "C:/Users/Public/TongYuan/.julia/miniforge3/Scripts;"
            f"{os.environ['PATH']}"
        )
    } 