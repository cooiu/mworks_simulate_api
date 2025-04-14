import subprocess
import os
from typing import Dict, Any, List, Tuple
from config import Config
from .process_manager import ProcessManager
import re
import logging

class SyslabExecutor:
    _process_manager = ProcessManager()

    '''检查代码中需要安装'''
    @staticmethod
    def check_required_packages(code: str) -> List[str]:
        # 正则表达式
        patterns = [
            r'using\s+([\w\.]+(?:\s*,\s*[\w\.]+)*)',
            r'import\s+([\w\.]+(?:\s*,\s*[\w\.]+)*)'
        ]
        required = set()
        init_package = ['TyPlot','TyBase','PyCall','TyMath']
        for pattern in patterns:
            for match in re.finditer(pattern, code):
                pkgs = re.split(r'\s*,\s*', match.group(1))
                for pkg in pkgs:
                    base = pkg.split('.')[0]
                    if base not in init_package:
                        required.add(base)
        return list(required)
    
    """安装多个包并返回汇总结果"""
    @staticmethod
    def ensure_packages(pkg_list: List[str], env: dict) -> Tuple[bool, str]:
        """安装多个包并返回汇总结果"""
        error_msgs = []
        success_pkgs = []
        
        # 安装包
        for pkg in pkg_list:
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
                if process.returncode == 0:
                    success_pkgs.append(pkg)
                    logging.info(f"Package {pkg} installed successfully")
                else:
                    error_msgs.append(f"{pkg}安装失败: {stderr}")
                    logging.error(f"Failed to install {pkg}: {stderr}")
            except Exception as e:
                error_msgs.append(f"{pkg}安装失败: {str(e)}")
                logging.error(f"Error installing {pkg}: {str(e)}")
        
        if error_msgs:
            return False, "\n".join(error_msgs)
        return True, f"成功安装所有包: {', '.join(success_pkgs)}"

    '''初始化会话，安装必要的包'''
    @staticmethod
    def create_session(session_id: str) -> Dict[str, Any]:
        """Create a new Julia session"""
        success = SyslabExecutor._process_manager.create_session(session_id)
        if not success:
            return {'error': 'Session already exists'}
        
        # 会话初始化
        init_code = """
        println("Initializing Julia session...")
        
        # 设置环境变量
        ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
        ENV["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        
        # 导入包 - 确保在全局范围内导入
        try
            using PyCall
            using TyPlot
            using TyBase
            using TyMath
            
            # 确保TyPlot正确加载
            if isdefined(Main, :TyPlot)
                println("TyPlot已加载")
            end
            
            println("所有包加载成功")
        catch e
            println("Error loading packages: " * string(e))
        end
        
        println("Julia会话初始化完成")
        """
        
        result = SyslabExecutor._process_manager.execute_code(session_id, init_code)
        if result.get('error'):
            SyslabExecutor._process_manager.terminate_session(session_id)
            return result
        
        return {'message': 'Session created successfully'}

    '''在现有进程中执行代码'''
    @staticmethod
    def execute_code(code: str, session_id: str = None) -> Dict[str, Any]:
        """Execute code in a Julia session"""
        try:
            results = {
                'images': [],
                'text': [],
                'error': None
            }

            # If no session_id provided, create a temporary one
            if not session_id:
                session_id = f"temp_{os.getpid()}"
                result = SyslabExecutor.create_session(session_id)
                if result.get('error'):
                    return {'error': f"无法创建临时会话: {result.get('error')}"}

            # 包管理 - 检查是否需要新的包
            packages = SyslabExecutor.check_required_packages(code)
            if packages:
                logging.info(f"需要安装新的包: {packages}")
                env = os.environ.copy()
                env.update(Config.ENV)
                success, msg = SyslabExecutor.ensure_packages(packages, env)
                if not success:
                    return {'error': f"包安装失败: {msg}"}

            # 构建执行代码
            temp_dir = os.path.abspath(Config.TEMP_DIR)
            os.makedirs(temp_dir, exist_ok=True)
            fig_path = os.path.join(temp_dir, f"output_{session_id}.svg")
            
            # 确保图形输出目录存在
            os.makedirs(os.path.dirname(fig_path), exist_ok=True)
            
            # 处理路径中的反斜杠
            fig_path = fig_path.replace('\\', '/')
            
            # 清空任何现有输出
            if session_id in SyslabExecutor._process_manager.output_queues:
                queue = SyslabExecutor._process_manager.output_queues[session_id]
                while not queue.empty():
                    queue.get_nowait()
            
            if session_id in SyslabExecutor._process_manager.error_queues:
                queue = SyslabExecutor._process_manager.error_queues[session_id]
                while not queue.empty():
                    queue.get_nowait()
            
            # 构建完整的执行代码
            full_code = f"""
            using TyPlot
            
            # 执行用户代码
            {code}

            # 尝试保存图形
            try
                fig = TyPlot.gcf()
                if fig !== nothing
                    TyPlot.saveas(fig, "{fig_path}")
                    println("图形已保存到: {fig_path}")
                else
                    println("没有找到活动的图形对象")
                end
            catch e
                println("保存图形出错: " * string(e))
            end
            
            # 确保输出被刷新
            flush(stdout)
            flush(stderr)
            """
            
            # Execute code in the session
            result = SyslabExecutor._process_manager.execute_code(session_id, full_code)
            
            if result.get('error'):
                return {'error': result['error']}
            
            # 过滤重复输出
            seen_lines = set()
            filtered_text = []
            for line in result.get('text', []):
                if line and line not in seen_lines:
                    seen_lines.add(line)
                    filtered_text.append(line)
            
            results['text'] = filtered_text
            
            # 处理图像 - 检测空图像
            if os.path.exists(fig_path):
                try:
                    with open(fig_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                        
                        # 检查SVG是否为空图像
                        is_empty_svg = False
                        
                        # 1. 检查文件大小
                        if len(svg_content) < 1200:  # 通常空SVG约1000-1200字节
                            # 2. 检查是否缺少绘图元素(path, rect 等)
                            if "<path" not in svg_content or ('id="patch_1"' in svg_content and 'id="patch_2"' not in svg_content):
                                is_empty_svg = True
                                
                        # 3. 额外检查，如果缺少绘图元素
                        if "<g id=\"axes_1\"" not in svg_content:
                            is_empty_svg = True
                            
                        if not is_empty_svg and "<svg" in svg_content:
                            results['images'].append({
                                'type': 'svg',
                                'data': svg_content
                            })
                            logging.info(f"生成了有效图形，大小: {len(svg_content)} 字节")
                        else:
                            logging.info(f"检测到空图像，大小: {len(svg_content)} 字节，不添加到结果中")
                    
                    os.remove(fig_path)
                except Exception as e:
                    logging.error(f"读取图像文件失败: {str(e)}")
                    results['error'] = f"读取图像文件失败: {str(e)}"
            else:
                logging.info("没有生成图形文件")
            
            # Clean up temporary session
            if session_id and session_id.startswith('temp_'):
                SyslabExecutor._process_manager.terminate_session(session_id)
            
            return results
            
        except Exception as e:
            logging.error(f"执行代码时发生错误: {str(e)}")
            return {
                'error': f"系统错误: {str(e)}",
                'text': [],
                'images': []
            }
        
    """结束会话进程"""
    @staticmethod
    def terminate_session(session_id: str) -> Dict[str, Any]:
        if not session_id:
            return {'error': 'No session ID provided'}
        
        SyslabExecutor._process_manager.terminate_session(session_id)
        return {'message': 'Session terminated successfully'}
