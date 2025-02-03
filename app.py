from flask import Flask, request, jsonify
from flask_cors import CORS
import io
import base64
import sys
import os
import subprocess
from config import Config

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': '没有提供代码'}), 400

        # 创建结果字典
        results = {
            'images': [],  # 存储图片的base64字符串
            'text': [],    # 存储文本结果
            'error': None  # 存储错误信息
        }

        try:
            print("开始执行代码...")
            # 将Julia代码写入临时文件，使用utf-8编码
            with open('temp_code.jl', 'w', encoding='utf-8') as f:
                f.write(code)

            # 使用Julia执行代码，指定编码
            env = os.environ.copy()
            env.update({
                "PYTHON": "C:/Users/Public/TongYuan/.julia/miniforge3/python.exe",
                "JULIA_DEPOT_PATH": "C:/Users/Public/TongYuan/.julia",
                "PATH": (
                    "C:/Users/Public/TongYuan/.julia/miniforge3;"
                    "C:/Users/Public/TongYuan/.julia/miniforge3/Scripts;"
                    f"{os.environ['PATH']}"
                ),
                "PYTHONIOENCODING": "utf-8"  # 设置Python IO编码
            })
            
            # 修改subprocess.Popen的参数
            process = subprocess.Popen(
                [Config.JULIA_PATH, 'temp_code.jl'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',  # 明确指定编码
                errors='replace'    # 处理无法解码的字符
            )
            
            stdout, stderr = process.communicate()
            
            # 处理标准输出
            if stdout:
                results['text'].append(stdout.strip())

            # 处理错误输出
            if stderr:
                results['error'] = stderr.strip()

            # 检查并读取.syslabfig文件
            if os.path.exists('trig_functions.syslabfig'):
                with open('trig_functions.syslabfig', 'rb') as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    results['images'].append({
                        'id': len(results['images']),
                        'data': f'data:image/png;base64,{img_base64}'
                    })
                # 删除临时文件
                os.remove('trig_functions.syslabfig')

        except Exception as e:
            results['error'] = str(e)
        finally:
            # 清理临时文件
            if os.path.exists('temp_code.jl'):
                os.remove('temp_code.jl')
            if os.path.exists('trig_functions.syslabfig'):
                try:
                    os.remove('trig_functions.syslabfig')
                except:
                    pass

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': f'请求处理错误: {str(e)}'}), 500

def check_julia_installation():
    """检查Julia是否正确安装"""
    if not os.path.exists(Config.JULIA_PATH):
        raise FileNotFoundError(f"找不到Julia可执行文件: {Config.JULIA_PATH}")
    
    try:
        process = subprocess.Popen(
            [Config.JULIA_PATH, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Julia执行错误: {stderr}")
        print(f"Julia版本: {stdout.strip()}")
        return True
    except Exception as e:
        print(f"检查Julia安装时出错: {str(e)}")
        return False

if __name__ == '__main__':
    if not check_julia_installation():
        print("Julia未正确安装或配置，请检查配置文件中的JULIA_PATH")
        sys.exit(1)
    app.run(debug=True, port=5000) 