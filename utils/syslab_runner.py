import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any
from config import Config
import base64

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
            # 设置环境变量
            ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
            ENV["SYSLAB_HOME"] = "D:/tools/MWorks/Syslab 2024b"
            ENV["TYMLANG_CONFIG_DIR"] = "C:/Users/Public/TongYuan/syslab-mlang"
            ENV["TYMLANG_INSTALL_DIR"] = "D:/tools/MWorks/Syslab 2024b/Tools/TyMLangDist"
            
            println("Current directory: ", pwd())
            println("Loading packages...")
            
            # 导入必要的包（这些包应该已经由 init_julia.py 安装）
            using TyBase
            using TyPlot
            using TyMath
            using Printf
            using Statistics
            using LinearAlgebra
            using DelimitedFiles
            
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
            
            logging.info("Starting code execution...")
            logging.info(f"Code to execute:\n{code}")
            
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
            
            stdout, stderr = process.communicate(timeout=Config.EXEC_TIMEOUT)
            
            logging.info(f"Execution completed with return code: {process.returncode}")
            logging.info(f"stdout:\n{stdout}")
            if stderr:
                logging.error(f"stderr:\n{stderr}")
            
            # 创建标准格式的返回结果
            results = {
                'images': [],
                'text': [],
                'error': None
            }
            
            # 处理标准输出
            if stdout:
                results['text'].append(stdout.strip())
            
            # 处理错误输出
            if stderr:
                results['error'] = stderr.strip()
            
            # 处理图片文件
            fig_file = os.path.join(Config.TEMP_DIR, 'trig_functions.syslabfig')
            if os.path.exists(fig_file):
                with open(fig_file, 'rb') as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    results['images'].append({
                        'id': len(results['images']),
                        'data': f'data:image/png;base64,{img_base64}'
                    })
                # 删除临时图片文件
                os.remove(fig_file)
            
            return results
                
        except Exception as e:
            logging.error(f"Error executing code: {str(e)}")
            return {
                'images': [],
                'text': [],
                'error': str(e)
            }
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)