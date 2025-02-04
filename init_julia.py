import subprocess
import os
from config import Config
import concurrent.futures
import logging

def install_package(pkg: str, env: dict) -> tuple:
    """安装单个Julia包"""
    try:
        cmd = f"""
        using Pkg
        println("Installing {pkg}...")
        Pkg.add("{pkg}")
        println("{pkg} installed successfully!")
        """
        
        process = subprocess.Popen(
            [Config.JULIA_PATH, "-e", cmd],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        stdout, stderr = process.communicate()
        return (pkg, True, stdout, stderr)
    except Exception as e:
        return (pkg, False, "", str(e))

def init_julia_env():
    """初始化 Julia 环境，并行安装必要的包"""
    print("开始初始化 Julia 环境...")
    
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
    
    # 创建临时目录
    os.makedirs(Config.TEMP_DIR, exist_ok=True)
    
    # 设置Python环境
    init_code = """
    ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
    println("Python environment set!")
    """
    
    print("设置Python环境...")
    process = subprocess.Popen(
        [Config.JULIA_PATH, "-e", init_code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()
    print(stdout)
    if stderr:
        print("错误:", stderr)
    
    # 要安装的包列表
    packages = [
        "PyCall",
        "TyPlot",
        "TyBase",
        "TyMath"
    ]
    
    print("\n并行安装包...")
    
    # 使用线程池并行安装包
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(install_package, pkg, env)
            for pkg in packages
        ]
        
        # 收集结果
        for future in concurrent.futures.as_completed(futures):
            pkg, success, stdout, stderr = future.result()
            if success:
                print(f"✓ {pkg} 安装成功")
                if stdout:
                    print(stdout)
            else:
                print(f"✗ {pkg} 安装失败")
                if stderr:
                    print(f"错误: {stderr}")
    
    # 构建 PyCall
    print("\n构建 PyCall...")
    build_code = """
    using Pkg
    println("Building PyCall...")
    Pkg.build("PyCall")
    println("PyCall built successfully!")
    """
    
    process = subprocess.Popen(
        [Config.JULIA_PATH, "-e", build_code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()
    print(stdout)
    if stderr:
        print("错误:", stderr)
    
    # 测试导入
    print("\n测试包导入...")
    test_code = """
    println("Testing imports...")
    using PyCall
    using TyPlot
    using TyBase
    using TyMath
    println("All packages imported successfully!")
    """
    
    process = subprocess.Popen(
        [Config.JULIA_PATH, "-e", test_code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()
    print(stdout)
    if stderr:
        print("错误:", stderr)
    
    print("\n初始化完成!")

if __name__ == "__main__":
    init_julia_env()