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

        env = os.environ.copy()
        env.update(Config.ENV)
        
        # 设置编码
        env["PYTHONIOENCODING"] = "utf-8"
        env["LANG"] = "en_US.UTF-8"
        env["LC_ALL"] = "en_US.UTF-8"
        
        # 设置Julia环境变量
        env["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        env["PLOTS_DEFAULT_BACKEND"] = "svg"
        env["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"

        # 预先安装和构建包
        self._pre_install_packages(env)
        
        # 使用 -i 参数启动交互式会话
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
        time.sleep(1)
        
        # 初始化Julia环境 - 只加载包，不安装
        init_code = """
        println("Initializing Julia environment...")
        
        # 设置环境变量
        ENV["PYTHON"] = "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe"
        ENV["JULIA_DEPOT_PATH"] = "C:/Users/Public/TongYuan/.julia"
        ENV["PLOTS_DEFAULT_BACKEND"] = "svg"
        
        # 导入必要的包
        println("Loading packages...")
        try
            using PyCall
            println("PyCall loaded")
        catch e
            println("Error loading PyCall: ", e)
        end
        
        try
            using Plots
            println("Plots loaded")
        catch e
            println("Error loading Plots: ", e)
        end
        
        try
            using TyPlot
            println("TyPlot loaded")
        catch e
            println("Error loading TyPlot: ", e)
        end
        
        try
            using TyBase
            println("TyBase loaded")
        catch e
            println("Error loading TyBase: ", e)
        end
        
        try
            using TyMath
            println("TyMath loaded")
        catch e
            println("Error loading TyMath: ", e)
        end
        
        println("Julia环境初始化完成")
        """
        
        try:
            process.stdin.write(init_code + "\n")
            process.stdin.flush()
            time.sleep(3)  # 等待初始化完成
        except Exception as e:
            logging.error(f"Error initializing Julia environment: {str(e)}")
            return False
            
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
            # Clear any existing output
            while not output_queue.empty():
                output_queue.get_nowait()
            while not error_queue.empty():
                error_queue.get_nowait()

            # Send code to process
            process.stdin.write(code + "\n")
            process.stdin.flush()

            # Collect output
            output = []
            error_output = []
            
            # 等待输出，最多等待10秒
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    # 检查标准输出
                    while True:
                        try:
                            line = output_queue.get_nowait()
                            output.append(line)
                            logging.debug(f"Session {session_id} stdout: {line}")
                        except queue.Empty:
                            break
                    
                    # 检查错误输出
                    while True:
                        try:
                            line = error_queue.get_nowait()
                            error_output.append(line)
                            logging.debug(f"Session {session_id} stderr: {line}")
                        except queue.Empty:
                            break
                    
                    # 如果没有新的输出，等待一小段时间
                    if not output and not error_output:
                        time.sleep(0.1)
                    
                except Exception as e:
                    logging.error(f"Error collecting output: {str(e)}")
                    break

            # 如果有错误输出，返回错误
            if error_output:
                return {
                    'error': '\n'.join(error_output),
                    'text': output
                }

            return {
                'text': output,
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