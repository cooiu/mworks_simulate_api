import subprocess
import os
from typing import Dict, Any, List, Tuple
from config import Config
from .process_manager import ProcessManager
import re
import logging
import time

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
        
        # # 会话初始化
        # init_code = """
        # println("Initializing Julia session...")
        
        # # 设置环境变量
        # ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
        # ENV["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        
        # # 导入包 - 确保在全局范围内导入
        # try
        #     using PyCall
        #     using TyPlot
        #     using TyBase
        #     using TyMath
            
        #     println("所有包加载成功")
        # catch e
        #     println("Error loading packages: " * string(e))
        # end
        
        # println("Julia会话初始化完成")
        # """
        
        # result = SyslabExecutor._process_manager.execute_code(session_id, init_code)
        # if result.get('error'):
        #     SyslabExecutor._process_manager.terminate_session(session_id)
        #     return result
        
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
            
            logging.info(f"当前会话ID: {session_id}")
   
            if os.path.exists(fig_path):
                try:
                    os.remove(fig_path)
                    logging.info(f"删除了已存在的图像文件: {fig_path}")
                    # 确保原图形输出目录已删除
                    logging.info(os.makedirs(os.path.dirname(fig_path), exist_ok=True)) 
                except Exception as e:
                    logging.warning(f"删除文件失败: {str(e)}")
            
            # # 处理路径中的反斜杠 - 规范化路径格式
            fig_path_julia = fig_path.replace('\\', '/')
            
            # # 清空任何现有输出
            # if session_id in SyslabExecutor._process_manager.output_queues:
            #     queue = SyslabExecutor._process_manager.output_queues[session_id]
            #     while not queue.empty():
            #         queue.get_nowait()
            
            # if session_id in SyslabExecutor._process_manager.error_queues:
            #     queue = SyslabExecutor._process_manager.error_queues[session_id]
            #     while not queue.empty():
            #         queue.get_nowait()
            
            # 构建完整的执行代码
            full_code = f"""
            # 加载必要的包
            using TyPlot

            plt_close()
            # 执行用户代码
            {code}

            saveas(gcf(), "{fig_path_julia}")
            plt_close()

            """
            # Execute code in the session
            result = SyslabExecutor._process_manager.execute_code(session_id, full_code)
            
            # 处理执行结果
            if result.get('error'):
                logging.error(f"执行代码错误: {result.get('error')}")
                results['error'] = result.get('error')
            
            if result.get('text'):
                # 过滤掉与图形相关的消息和多余的信息
                text_output = []
                graph_messages = []
                for line in result.get('text', []):
                    # 过滤掉与图形相关的消息
                    if any(msg in line for msg in ["图形已保存", "图形保存完成", 
                                                  "VERIFY_SUCCESS", "VERIFY_FAIL", 
                                                  "文件大小", "PLOT_DEBUG", "获取到图形对象"]):
                        graph_messages.append(line)
                    # 过滤掉矢量数据描述行
                    elif any(keyword in line for keyword in ["-element Vector{", "PyObject", "elements"]):
                        continue
                    # 过滤掉变量的定义行
                    elif ":" in line and not "println" in line.lower():
                        continue
                    else:
                        # 检查是否是纯数值输出（比如println的结果）
                        stripped_line = line.strip()
                        if stripped_line and (stripped_line.replace('.', '', 1).replace('-', '', 1).isdigit() or 
                                            stripped_line in ['true', 'false']):
                            text_output.append(stripped_line)
                        # 否则，检查是否是有意义的文本输出
                        elif len(stripped_line) > 0 and not stripped_line.startswith('[') and not stripped_line.endswith(']'):
                            text_output.append(stripped_line)
                
                results['text'] = text_output
                logging.info(f"收集到文本输出: {len(text_output)} 行")
                logging.info(f"图形相关消息: {graph_messages}")
            
            # 等待文件写入完成
            max_wait_time = 5  # 最大等待时间（秒）
            wait_interval = 0.5  # 检查间隔（秒）
            total_wait = 0
            found_svg = None
            
            while total_wait < max_wait_time:
                if os.path.exists(fig_path):
                    # 检查文件是否可读且大小稳定
                    try:
                        with open(fig_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content and len(content) > 0:
                                found_svg = fig_path
                                logging.info(f"找到有效的SVG文件: {fig_path}, 大小: {len(content)} 字节")
                                break
                    except Exception as e:
                        logging.info(f"文件 {fig_path} 暂时不可读: {str(e)}")
                
                if found_svg:
                    break
                    
                logging.info(f"等待文件创建... ({total_wait:.1f}/{max_wait_time} 秒)")
                time.sleep(wait_interval)
                total_wait += wait_interval
            
            # 处理找到的SVG文件
            if found_svg:
                try:
                    # 确保文件完全写入
                    time.sleep(0.5)
                    
                    with open(found_svg, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                        content_size = len(svg_content)
                        logging.info(f"SVG文件大小: {content_size} 字节")
                        
                        # 检查SVG内容是否有效
                        has_rect_tag = '<rect' in svg_content
                        
                        # 只要文件大小合理且包含SVG标签，就认为有效
                        if has_rect_tag and content_size > 1200:
                            results['images'].append({
                                'type': 'svg',
                                'data': svg_content
                            })
                            logging.info(f"成功添加SVG图像，大小: {content_size} 字节")
                        else:
                            logging.warning(f"SVG文件内容可能无效: has_svg_tag={has_rect_tag}, content_size={content_size}")
                            # 保存一份以便调试
                            # debug_path = f"{found_svg}.debug"
                            # with open(debug_path, 'w', encoding='utf-8') as df:
                            #     df.write(svg_content)
                            # logging.info(f"已保存SVG内容到调试文件: {debug_path}")
                    
                    try:
                        os.remove(found_svg)
                        logging.info(f"已删除SVG文件: {found_svg}")
                    except Exception as e:
                        logging.warning(f"删除SVG文件失败: {str(e)}")
                except Exception as e:
                    logging.error(f"处理SVG文件失败: {str(e)}", exc_info=True)
                    results['error'] = f"处理图像文件失败: {str(e)}"
            else:
                logging.warning(f"未找到任何SVG图像文件")
                # 列出临时目录内容
                try:
                    dir_contents = sorted(os.listdir(temp_dir))
                    svg_files = [f for f in dir_contents if f.endswith('.svg')]
                    logging.info(f"目录中的所有文件: {dir_contents}")
                    logging.info(f"SVG文件: {svg_files}")
                except Exception as e:
                    logging.warning(f"无法列出目录内容: {str(e)}")
            
            # Clean up temporary session
            if session_id and session_id.startswith('temp_'):
                SyslabExecutor._process_manager.terminate_session(session_id)
            
            return results
            
        except Exception as e:
            logging.error(f"执行代码时发生错误: {str(e)}", exc_info=True)
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
