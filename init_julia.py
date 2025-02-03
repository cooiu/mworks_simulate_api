import subprocess
import os
from config import Config

def init_julia_env():
    """初始化 Julia 环境，安装必要的包"""
    print("开始初始化 Julia 环境...")
    
    # 创建初始化脚本
    init_code = """
    ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
    
    using Pkg
    
    # 添加必要的包
    println("Installing packages...")
    
    packages = [
        "PyCall",
        "TyBase",
        "TyPlot",
        "TyMath",
        "Printf",
        "Statistics",
        "LinearAlgebra",
        "DelimitedFiles"
    ]

    for pkg in packages
        println("Installing $pkg...")
        Pkg.add(pkg)
    end
    
    println("Building PyCall...")
    Pkg.build("PyCall")
    
    # 测试导入
    println("\\nTesting imports...")
    using PyCall
    using TyPlot
    using TyMath
    using Printf
    using Statistics
    using LinearAlgebra
    using DelimitedFiles
    
    println("\\nInstallation completed!")
    """
    
    # 保存到临时文件
    init_file = os.path.join(Config.TEMP_DIR, "init.jl")
    os.makedirs(Config.TEMP_DIR, exist_ok=True)
    
    with open(init_file, "w", encoding="utf-8") as f:
        f.write(init_code)
    
    # 设置环境变量
    env = os.environ.copy()
    env.update({
        "PYTHON": "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe",
        "JULIA_DEPOT_PATH": "C:/Users/Public/TongYuan/.julia",
        "PATH": (
            "C:/Users/Public/TongYuan/.julia/miniforge3;"
            "C:/Users/Public/TongYuan/.julia/miniforge3/Scripts;"
            f"{os.environ['PATH']}"
        )
    })
    
    # 执行初始化
    print("执行初始化脚本...")
    process = subprocess.Popen(
        [Config.JULIA_PATH, init_file],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    
    stdout, stderr = process.communicate()
    print("\n输出:")
    print(stdout)
    
    if stderr:
        print("\n错误:")
        print(stderr)
    
    if process.returncode == 0:
        print("\n初始化成功!")
    else:
        print("\n初始化失败!")

if __name__ == "__main__":
    init_julia_env() 