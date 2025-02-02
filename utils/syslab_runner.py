import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any
from config import Config

class SyslabExecutor:
    @staticmethod
    def execute_code(code: str) -> Dict[str, Any]:
        """执行 Julia 代码并返回结果"""
        try:
            # 确保临时目录存在
            os.makedirs(Config.TEMP_DIR, exist_ok=True)
            
            # 创建临时文件存储代码
            temp_file = Path(Config.TEMP_DIR) / "temp_code.jl"
            
            # 添加必要的包导入和初始化代码
            full_code = """
            # 设置 Python 环境
            ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
            
            # 设置环境变量
            ENV["SYSLAB_HOME"] = "D:/tools/MWorks/Syslab 2024b"
            ENV["TYMLANG_CONFIG_DIR"] = "C:/Users/Public/TongYuan/syslab-mlang"
            ENV["TYMLANG_INSTALL_DIR"] = "D:/tools/MWorks/Syslab 2024b/Tools/TyMLangDist"
            
            println("Current directory: ", pwd())
            println("Loading packages...")
            
            # 导入必要的包
            using TyBase
            using TyPlot
            
            # 设置工作目录
            cd("{}")
            println("Working directory: ", pwd())
            
            # 执行用户代码
            println("Executing user code:")
            println("-" ^ 40)
            
            {}
            
            println("-" ^ 40)
            println("Execution completed!")
            """.format(Config.TEMP_DIR.replace("\\", "/"), code)
            
            # 保存代码到临时文件
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(full_code)
            
            # 构造执行命令
            cmd = [
                Config.JULIA_PATH,
                "--project=D:/tools/MWorks/Syslab 2024b/Tools/TyMLangDist",
                str(temp_file)
            ]
            
            # 设置环境变量
            env = os.environ.copy()
            env.update({
                "PYTHON": "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe",
                "JULIA_DEPOT_PATH": "C:/Users/Public/TongYuan/.julia",
                "SYSLAB_HOME": "D:/tools/MWorks/Syslab 2024b",
                "TYMLANG_CONFIG_DIR": "C:/Users/Public/TongYuan/syslab-mlang",
                "TYMLANG_INSTALL_DIR": "D:/tools/MWorks/Syslab 2024b/Tools/TyMLangDist",
                "PATH": (
                    "C:/Users/Public/TongYuan/.julia/miniforge3;"
                    "C:/Users/Public/TongYuan/.julia/miniforge3/Scripts;"
                    f"{os.environ['PATH']};"
                    "D:/tools/MWorks/Syslab 2024b/Bin"
                )
            })
            
            logging.info(f"Executing command: {' '.join(cmd)}")
            logging.info(f"Working directory: {Config.TEMP_DIR}")
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                cwd=Config.TEMP_DIR
            )
            
            try:
                stdout, stderr = process.communicate(timeout=Config.EXEC_TIMEOUT)
                
                # 记录输出
                logging.info(f"stdout: {stdout}")
                if stderr:
                    logging.error(f"stderr: {stderr}")
                
                if process.returncode == 0:
                    # 检查图片是否生成
                    png_file = os.path.join(Config.TEMP_DIR, "test.png")
                    if os.path.exists(png_file):
                        logging.info(f"Plot generated: {png_file}")
                    
                    return {
                        "status": "success",
                        "output": stdout,
                        "error": None
                    }
                else:
                    error_msg = stderr or stdout or "Unknown error occurred"
                    return {
                        "status": "error",
                        "output": None,
                        "error": error_msg
                    }
                    
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "status": "error",
                    "output": None,
                    "error": "Execution timeout"
                }
                
        except Exception as e:
            logging.error(f"Error executing code: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": str(e)
            }