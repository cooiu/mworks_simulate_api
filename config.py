import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # syslab 可执行文件路径
    SYSLAB_PATH = os.getenv("SYSLAB_PATH", r"D:\tools\MWorks\Syslab 2024b\Bin\syslab.exe")
    
    # Julia 可执行文件路径
    JULIA_PATH = os.getenv("JULIA_PATH", r"C:/Users/Public/TongYuan/julia-1.9.3/bin/julia.exe")
    
    # 日志路径
    LOG_PATH = os.getenv("LOG_PATH", r"C:/Users/Public/TongYuan/logs")
    
    # 模拟结果路径
    SIMULATION_RESULT_PATH = os.getenv("SIMULATION_RESULT_PATH", 
                                     r"C:/Users/Public/TongYuan/syslab-julia/Simulation")
    
    # 临时文件目录 (使用绝对路径)
    TEMP_DIR = os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp"))
    
    # 执行超时时间（秒）
    EXEC_TIMEOUT = int(os.getenv("EXEC_TIMEOUT", 120)) 