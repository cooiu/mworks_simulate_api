import subprocess
import os
from typing import Dict, Any, List, Tuple
from config import Config
import re

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
            if pkg_name not in ["TyBase","TyPlot", "TyMath", "PyCall"]:
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
        try:
            results = {
                'images': [],
                'text': [],
                'error': None
            }
            
            # 使用临时目录存储图片文件
            temp_dir = os.path.abspath(Config.TEMP_DIR)
            os.makedirs(temp_dir, exist_ok=True)
            # fig_path = os.path.join(temp_dir, "output.svg")
            
            # 构建完整代码
            full_code = """
            using TyPlot
            
            println("-"^40)
            
            {}

            if gcf() !== nothing
                saveas(gcf(), "output.svg")
                println("图形已保存为SVG格式")
            end

            println("-"^40)
            """.format(code)
            
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

            # 执行代码
            process = subprocess.Popen(
                [Config.JULIA_PATH, "-e", full_code],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate()
            
            if stdout:
                results['text'] = [line.strip() for line in stdout.split('\n') if line.strip()]
            
            if stderr:
                results['error'] = stderr.strip()
                print(f"Julia错误: {stderr}")  # 打印错误信息
            
            # 检查当前工作目录下的图片文件
            fig_path = "output.svg"  # 直接在当前目录查找
            print(f"检查图片文件: {fig_path}")
            
            if os.path.exists(fig_path):
                print("找到图片文件")
                try:
                    with open(fig_path, 'r', encoding='utf-8') as f:
                        svg_data = f.read()
                        results['images'].append({
                            'id': len(results['images']),
                            'type': 'svg',
                            'data': svg_data
                        })
                    # 读取完成后删除文件
                    os.remove(fig_path)
                    print("图片文件已删除")
                except Exception as e:
                    print(f"处理图片文件时出错: {e}")
            else:
                print("图片文件不存在")
            
            return results
            
        except Exception as e:
            print(f"Python错误: {str(e)}")  # 打印错误信息
            return {
                'images': [], 
                'text': [], 
                'error': f"执行错误: {str(e)}"
            }
