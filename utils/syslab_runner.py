import subprocess
import os
from typing import Dict, Any, List, Tuple
from config import Config
from .process_manager import ProcessManager
import re
import logging
import time
import pathlib

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
            # logging.info(f"主图像路径: {fig_path} (Julia格式: {fig_path_julia})")
            
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

            plt_close()
            # 执行用户代码
            {code}

            saveas(gcf(), "{fig_path_julia}")
            plt_close()

            """
            print(full_code)
            # Execute code in the session
            result = SyslabExecutor._process_manager.execute_code(session_id, full_code)
            
            # 处理执行结果
            if result.get('error'):
                logging.error(f"执行代码错误: {result.get('error')}")
                results['error'] = result.get('error')
            
            # 提取输出文本，但过滤掉图形保存相关消息
            if result.get('text'):
                text_output = []
                for line in result.get('text', []):
                    if any(keyword in line for keyword in [
                        "VERIFY_SUCCESS", "VERIFY_FAIL", "图形将保存到", "保存图形时出错",
                        "正在保存图形", "图形已保存到", "准备执行用户代码", "图形保存完成", 
                        "保存图形到", "获取到图形对象", "文件大小:"
                    ]):
                        logging.info(f"Julia输出: {line}")
                    else:
                        text_output.append(line)
                
                results['text'] = text_output
                logging.info(f"收集到文本输出: {len(text_output)} 行")
            
            # 为确保文件已写入，等待一小段时间
            time.sleep(5)

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
                try:
                    os.remove(fig_path)
                    logging.info(f"已删除SVG文件: {fig_path}")
                except Exception as e:
                    logging.warning(f"删除SVG文件失败: {str(e)}")

            # # 处理找到的图像
            # if fig_path:
            #     try:
            #         with open(fig_path, 'r', encoding='utf-8') as f:
            #             svg_content = f.read()
            #             content_size = len(svg_content)
                        
            #             logging.info(f"SVG文件大小: {content_size} 字节")
                        
            #             # 检测空图像：没有path标签或文件太小
            #             is_empty_figure = (content_size < 1200)
                        
            #             logging.info(f"空图像检测结果: {is_empty_figure}")
                        
            #             if not is_empty_figure:
            #                 # 有效的SVG文件，添加到结果中
            #                 results['images'].append({
            #                     'type': 'svg',
            #                     'data': svg_content
            #                 })
            #                 logging.info(f"成功添加SVG图像到结果, 来自: {fig_path}")
            #             else:
            #                 logging.warning(f"SVG图像被判定为空或无效，大小: {content_size} 字节")
            #                 # 保存文件以便调试
            #                 debug_path = f"{fig_path}.debug"
            #                 with open(debug_path, 'w', encoding='utf-8') as df:
            #                     df.write(svg_content)
            #                 logging.info(f"已保存SVG到调试文件: {debug_path}")
                    
            #             try:
            #                 os.remove(fig_path)
            #                 logging.info(f"已删除SVG文件: {fig_path}")
            #             except Exception as e:
            #                 logging.warning(f"删除SVG文件失败: {str(e)}")
                    
            #     except Exception as e:
            #         logging.error(f"读取SVG文件失败: {str(e)}", exc_info=True)
            #         results['error'] = f"处理图像文件失败: {str(e)}"
            # else:
            #     logging.warning(f"未找到任何SVG图像文件")
            #     try:
            #         dir_contents = os.listdir(temp_dir)
            #         svg_files = [f for f in dir_contents if f.endswith('.svg')]
            #         logging.info(f"目录 {temp_dir} 中的SVG文件: {svg_files}")
            #     except Exception as e:
            #         logging.warning(f"无法列出目录内容: {str(e)}")
            
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
