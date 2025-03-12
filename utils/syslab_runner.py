import subprocess
import os
from typing import Dict, Any, List, Tuple
from config import Config
from init_julia import install_package
import re

class SyslabExecutor:
    @staticmethod
    def check_required_packages(code: str) -> List[str]:
        patterns = [
            r'using\s+([\w\.]+(?:\s*,\s*[\w\.]+)*)',
            r'import\s+([\w\.]+(?:\s*,\s*[\w\.]+)*)'
        ]
        
        required = set()
        base_pkgs = {"TyBase", "TyPlot", "TyMath", "PyCall"}
        
        for pattern in patterns:
            for match in re.finditer(pattern, code):
                pkgs = re.split(r'\s*,\s*', match.group(1))
                for pkg in pkgs:
                    base = pkg.split('.')[0]
                    if base not in base_pkgs:
                        required.add(base)
        
        return list(required)

    @staticmethod
    def ensure_packages(pkg_list: List[str], env: dict) -> Tuple[bool, str]:
        """安装多个包并返回汇总结果"""
        error_msgs = []
        for pkg in pkg_list:
            success, _, stdout, stderr = install_package(pkg, env)
            if not success:
                error_msgs.append(f"{pkg}安装失败: {stderr or stdout}")
        
        if error_msgs:
            return False, "\n".join(error_msgs)
        return True, "成功安装所有包"

    @staticmethod
    def execute_code(code: str) -> Dict[str, Any]:
        try:
            results = {
                'images': [],
                'text': [],
                'error': None
            }

            # 初始化环境
            temp_dir = os.path.abspath(Config.TEMP_DIR)
            os.makedirs(temp_dir, exist_ok=True)
            env = os.environ.copy()
            env.update(Config.ENV)
            fig_path = os.path.join(temp_dir, "output.svg")
            
            # 包管理
            packages = SyslabExecutor.check_required_packages(code)
            success, msg =SyslabExecutor.ensure_packages(packages, env)
            if not success:
                return {'error': f"包安装失败: {msg}"}
            
            # 构建执行代码
            full_code = """
            using TyPlot
            
            {}
                
            if gcf() !== nothing
                saveas(gcf(), "{}")
            end

            """.format(code,fig_path.replace('\\', '/'))
            print(full_code)
            
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
            print(stdout,"标准输出")
            if stdout:
                results['text'] = [line.strip() for line in stdout.split('\n') if line.strip()]
            
            if stderr:
                results['error'] = stderr.strip()
                print(f"Julia错误: {stderr}")  # 打印错误信息
            
            # 处理图像
            if os.path.exists(fig_path):
                with open(fig_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                    # 检查 SVG 内容是否为空或只包含基本标签
                    if len(svg_content.strip()) < 100 or "<rect" not in svg_content:
                        results['images'] = []
                    else:
                        results['images'].append({
                            'type': 'svg',
                            'data': svg_content
                        })
                os.remove(fig_path)
            
            return results
            
        except Exception as e:
            return {
                'error': f"系统错误: {str(e)}",
                'text': [],
                'images': []
            }
