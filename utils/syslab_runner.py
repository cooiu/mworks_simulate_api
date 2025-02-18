import subprocess
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import Config
import base64
import re
import time

class SyslabExecutor:
    @staticmethod
    def check_required_packages(code: str) -> List[str]:
        """检查代码中需要的额外包"""
        packages = []
        
        # 使用正则表达式匹配 import 和 using 语句
        import_pattern = r'(?:import|using)\s+([A-Za-z][A-Za-z0-9_]*)'
        matches = re.finditer(import_pattern, code)
        
        for match in matches:
            pkg_name = match.group(1)
            # 排除已在初始化时安装的基础包
            if pkg_name not in ["TyBase", "TyPlot", "TyMath", "PyCall"]:
                packages.append(pkg_name)
        
        return list(set(packages))  # 去重

    @staticmethod
    def ensure_packages(packages: List[str], env: dict) -> Tuple[bool, str]:
        """确保包已安装"""
        if not packages:  # 如果没有额外的包需要安装
            return True, "No additional packages needed"
            
        try:
            # 构建安装代码
            install_code = """
            using Pkg
            
            function ensure_package(pkg)
                if Base.find_package(pkg) === nothing
                    println("Installing $pkg...")
                    Pkg.add(pkg)
                    println("$pkg installed successfully!")
                else
                    println("$pkg is already installed")
                end
            end
            
            for pkg in ["{}"]
                try
                    ensure_package(pkg)
                catch e
                    println("Error installing $pkg: $e")
                    exit(1)
                end
            end
            """.format('","'.join(packages))
            
            process = subprocess.Popen(
                [Config.JULIA_PATH, "-e", install_code],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                return False, f"包安装失败: {stderr or stdout}"
            return True, stdout
        except Exception as e:
            return False, f"包安装过程出错: {str(e)}"

    @staticmethod
    def execute_code(code: str) -> Dict[str, Any]:
        """执行 Julia 代码并返回结果"""
        try:
            # 确保临时目录存在
            os.makedirs(Config.TEMP_DIR, exist_ok=True)
            
            # 检查需要的额外包
            required_packages = SyslabExecutor.check_required_packages(code)
            if required_packages:
                logging.info(f"Additional packages required: {required_packages}")
            
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
            
            # 如果有额外的包，确保它们已安装
            if required_packages:
                success, message = SyslabExecutor.ensure_packages(required_packages, env)
                if not success:
                    return {
                        'images': [],
                        'text': [],
                        'error': message
                    }
                logging.info("Additional packages installation successful")
            
            # 创建临时文件存储代码
            temp_file = Path(Config.TEMP_DIR) / "temp_code.jl"
            
            # 添加必要的包导入和初始化代码
            full_code = """
            using TyPlot
            using TyBase

            # 执行用户代码:
            println("Executing user code:")
            println("-"^40)
            
            {}

            # 如果有图形，保存为图片
            if gcf() !== nothing
                savefig("output.syslabfig")
                println("图形已保存")
            end

            println("-"^40)
            println("Execution completed!")
            """.format(code)
            
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
            
            # 执行代码并获取输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env,
                cwd=Config.TEMP_DIR
            )
            
            # 读取输出
            stdout, stderr = process.communicate()
            
            # 创建结果字典
            results = {
                'images': [],
                'text': [],
                'error': None,
                'plot_window': True  # 标记需要显示图形窗口
            }
            
            # 处理文本输出
            if stdout:
                results['text'] = [line.strip() for line in stdout.split('\n') if line.strip()]
            
            # 处理错误输出
            if stderr:
                results['error'] = stderr.strip()
            
            # 处理图形文件
            fig_path = os.path.join(Config.TEMP_DIR, "output.syslabfig")
            if os.path.exists(fig_path):
                with open(fig_path, 'rb') as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    results['images'].append({
                        'id': len(results['images']),
                        'data': f'data:image/png;base64,{img_base64}'
                    })
            
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
