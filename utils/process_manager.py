import subprocess
import os
from typing import Dict
from config import Config
import threading
import queue
import logging
import time

class ProcessManager:
    _instance = None  # 存储单例实例
    _lock = threading.Lock()  # 线程锁，确保多线程环境下单例创建的原子性    

    def __new__(cls):
        with cls._lock:  # 加锁，确保线程安全
            if cls._instance is None:  # 如果实例不存在
                cls._instance = super(ProcessManager, cls).__new__(cls)  # 创建实例
            return cls._instance  # 返回实例（无论新旧）

    def __init__(self):
        if not hasattr(self, 'initialized'):  # 防止重复初始化
            self.processes: Dict[str, subprocess.Popen] = {}  # 存储子进程
            self.output_queues: Dict[str, queue.Queue] = {}   # 存储子进程标准输出队列
            self.error_queues: Dict[str, queue.Queue] = {}    # 存储子进程错误输出队列
            self.initialized = True  # 标记已初始化

    def create_session(self, session_id: str) -> bool:
        """Create a new Julia process for a session"""
        if session_id in self.processes:
            return False

        # 记录开始时间
        start_time = time.time()
        logging.info(f"开始创建Julia会话 {session_id}...")

        env = os.environ.copy()
        env.update(Config.ENV)
        
        # 设置编码
        env["PYTHONIOENCODING"] = "utf-8"
        env["LANG"] = "en_US.UTF-8"
        env["LC_ALL"] = "en_US.UTF-8"
        
        # 设置Julia环境变量
        env["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        env["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"

        # 预先安装和构建包
        self._pre_install_packages(env)
        
        # 使用 -i 参数启动交互式会话
        process_start_time = time.time()
        logging.info(f"启动Julia进程...")
        
        process = subprocess.Popen(
            [Config.JULIA_PATH, "-i"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )

        process_time = time.time() - process_start_time
        logging.info(f"Julia进程启动耗时: {process_time:.2f}秒")

        self.processes[session_id] = process
        self.output_queues[session_id] = queue.Queue()
        self.error_queues[session_id] = queue.Queue()

        # 启动输出和错误读取线程
        threading.Thread(
            target=self._read_output,
            args=(session_id, process.stdout, self.output_queues[session_id]),
            daemon=True
        ).start()

        threading.Thread(
            target=self._read_output,
            args=(session_id, process.stderr, self.error_queues[session_id]),
            daemon=True
        ).start()

        # 等待进程初始化
        # time.sleep(1)
        
        # 初始化Julia环境
        init_start_time = time.time()
        logging.info("开始初始化Julia环境...")
        
        init_code = """
        println("正在初始化Julia环境...")
        
        # 设置环境变量
        ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
        ENV["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        
        # 导入必要的包 - 确保在全局作用域中
        println("正在加载包...")
        
        try
            using PyCall
            println("PyCall 已加载")
        catch e
            println("加载 PyCall 失败: " * string(e))
        end
        
        try
            using TyPlot
            println("TyPlot loaded")
        catch e
            println("加载 TyPlot 失败: " * string(e))
        end
        
        try
            using TyBase
            println("TyBase 已加载")
        catch e
            println("加载 TyBase 失败: " * string(e))
        end
        
        try
            using TyMath
            println("TyMath 已加载")
        catch e
            println("加载 TyMath 失败: " * string(e))
        end
        
        println("Julia环境初始化完成!")
        """
        
        try:
            process.stdin.write(init_code + "\n")
            process.stdin.flush()
            
            # 等待初始化完成，同时收集输出
            wait_time = 5  # 初始等待时间
            max_wait_time = 60  # 最大等待时间
            elapsed = 0
            
            output_queue = self.output_queues[session_id]
            while elapsed < max_wait_time:
                # 检查是否收到初始化完成的消息
                init_completed = False
                while not output_queue.empty():
                    line = output_queue.get_nowait()
                    if "Julia环境初始化完成" in line:
                        init_completed = True
                        break
                
                if init_completed:
                    break
                    
                time.sleep(1)
                elapsed += 1
                
                # 每10秒输出一次等待信息
                if elapsed % 10 == 0:
                    logging.info(f"已等待Julia环境初始化 {elapsed} 秒...")
            
            init_time = time.time() - init_start_time
            logging.info(f"Julia环境初始化耗时: {init_time:.2f}秒")
            
        except Exception as e:
            logging.error(f"Error initializing Julia environment: {str(e)}")
            return False
            
        # 计算总耗时
        total_time = time.time() - start_time
        logging.info(f"会话 {session_id} 创建完成，总耗时: {total_time:.2f}秒")
        
        return True
        
    def _pre_install_packages(self, env):
        """预安装所需的包 - 使用与ts.py相同的方法"""
        logging.info("Pre-installing packages...")
        
        # 设置Python环境
        init_code = """
        ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
        println("Python environment set!")
        """
        
        process = subprocess.Popen(
            [Config.JULIA_PATH, "-e", init_code],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        logging.info(f"Python environment setup: {stdout}")
        if stderr:
            logging.error(f"Error setting Python env: {stderr}")
        
        # 安装包
        packages = ["PyCall", "TyPlot", "TyBase", "TyMath"]
        for pkg in packages:
            self._install_single_package(pkg, env)
        
        # 构建 PyCall
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
        logging.info(f"PyCall build: {stdout}")
        if stderr:
            logging.warning(f"PyCall build warning: {stderr}")
    
    def _install_single_package(self, pkg, env):
        """安装单个Julia包 - 与ts.py中相同的方法"""
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
            if stdout:
                logging.info(f"Package {pkg}: {stdout}")
            if stderr:
                logging.warning(f"Package {pkg} warning: {stderr}")
                
        except Exception as e:
            logging.error(f"Error installing {pkg}: {str(e)}")

    def _read_output(self, session_id: str, pipe, output_queue: queue.Queue):
        """Read output from the process in a separate thread"""
        while True:
            try:
                line = pipe.readline()
                if not line and self.processes[session_id].poll() is not None:
                    break
                if line:
                    output_queue.put(line.strip())
            except Exception as e:
                logging.error(f"Error reading output for session {session_id}: {str(e)}")
                break

    def execute_code(self, session_id: str, code: str) -> Dict:
        """Execute code in the specified session"""
        if session_id not in self.processes:
            return {'error': 'Session not found'}

        process = self.processes[session_id]
        output_queue = self.output_queues[session_id]
        error_queue = self.error_queues[session_id]

        try:
            # 彻底清空现有输出
            logging.debug(f"清空会话 {session_id} 的输出队列")
            while not output_queue.empty():
                output_queue.get_nowait()
            while not error_queue.empty():
                error_queue.get_nowait()
            
            # 发送一个清空命令到Julia进程
            process.stdin.write("clc\n")
            process.stdin.flush()
            
            # 等待清空标记被处理
            timeout = time.time() + 1.0
            while time.time() < timeout:
                try:
                    line = output_queue.get_nowait()
                    if "clc" in line:
                        break
                except queue.Empty:
                    time.sleep(0.1)
            
            # 再次清空，确保没有残留输出
            while not output_queue.empty():
                output_queue.get_nowait()
            while not error_queue.empty():
                error_queue.get_nowait()

            # 预处理代码：检查是否有分号结尾的行
            lines = code.strip().split('\n')
            semicolon_lines = []
            processed_code = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.endswith(';'):
                    semicolon_lines.append(i)
                processed_code.append(line)
            
            # 记录包含分号的行，以便后续过滤对应输出
            logging.debug(f"发现{len(semicolon_lines)}行代码以分号结尾")
            
            # 发送代码到进程
            logging.debug(f"发送代码到会话 {session_id}")
            process.stdin.write('\n'.join(processed_code) + "\n")
            process.stdin.flush()

            # 收集输出
            output = []
            error_output = []
            
            # 增加等待输出的时间，因为绘图操作可能比较耗时
            max_wait_time = 15  # 等待15秒
            output_idle_time = 1.0  # 如果1秒内没有新输出，认为完成
            
            start_time = time.time()
            last_output_time = start_time
            
            # 跟踪已看到的输出行，避免重复
            seen_stdout = set()
            seen_stderr = set()
            
            logging.debug(f"等待会话 {session_id} 的输出")
            while time.time() - start_time < max_wait_time:
                output_received = False
                
                try:
                    # 检查标准输出
                    while True:
                        try:
                            line = output_queue.get_nowait()
                            if line and line not in seen_stdout:  # 避免重复输出
                                # 跳过特殊标记
                                if "clc" not in line:
                                    seen_stdout.add(line)
                                    
                                    # 记录原始输出行，用于调试
                                    logging.debug(f"原始输出行 [{len(line)}]: '{line}'")
                                    
                                    # 跳过Julia提示符
                                    if line.strip().startswith("julia>"):
                                        logging.debug(f"跳过Julia提示符: {line}")
                                        continue
                                    
                                    # 检查是否是警告或系统消息
                                    if "DeprecationWarning" in line or "WARNING" in line:
                                        logging.debug(f"跳过警告信息: {line}")
                                        continue
                                    
                                    # 保留所有输出 - 不再对println输出进行过滤
                                    output.append(line)
                                    output_received = True
                                    last_output_time = time.time()
                                    logging.debug(f"Session {session_id} stdout: {line}")
                        except queue.Empty:
                            break
                    
                    # 检查错误输出
                    while True:
                        try:
                            line = error_queue.get_nowait()
                            if line and line not in seen_stderr:  # 避免重复输出
                                seen_stderr.add(line)
                                error_output.append(line)
                                output_received = True
                                last_output_time = time.time()
                                logging.debug(f"Session {session_id} stderr: {line}")
                        except queue.Empty:
                            break
                    
                    # 如果已经有输出，并且有一段时间没有新的输出，认为执行完成
                    if (output or error_output) and time.time() - last_output_time > output_idle_time:
                        break
                    
                    # 如果没有新的输出，等待一小段时间
                    if not output_received:
                        time.sleep(0.1)
                    
                except Exception as e:
                    logging.error(f"Error collecting output: {str(e)}")
                    break
            
            logging.debug(f"会话 {session_id} 执行完成，收集到 {len(output)} 行输出和 {len(error_output)} 行错误")

            # 如果有错误输出，返回错误
            if error_output:
                return {
                    'error': '\n'.join(error_output),
                    'text': output
                }

            # 过滤掉Julia REPL提示符等不需要的输出
            filtered_output = []
            for line in output:
                if not line.startswith("julia>") and "DeprecationWarning" not in line:
                    filtered_output.append(line)

            return {
                'text': filtered_output,
                'error': None
            }

        except Exception as e:
            logging.error(f"Error executing code in session {session_id}: {str(e)}")
            return {
                'error': f"Execution error: {str(e)}",
                'text': []
            }

    def terminate_session(self, session_id: str):
        """Terminate a session and its process"""
        if session_id in self.processes:
            process = self.processes[session_id]
            try:
                # 发送退出命令
                process.stdin.write("exit()\n")
                process.stdin.flush()
            except:
                pass
            finally:
                process.terminate()
                process.wait()
                del self.processes[session_id]
                del self.output_queues[session_id]
                del self.error_queues[session_id]

    def cleanup(self):
        """Cleanup all processes"""
        for session_id in list(self.processes.keys()):
            self.terminate_session(session_id) 