from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from utils.syslab_runner import SyslabExecutor

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': '没有提供代码'}), 400

        logging.info("Received code execution request")
        logging.info(f"Code:\n{code}")
        
        # 使用 SyslabExecutor 执行代码
        result = SyslabExecutor.execute_code(code)
        
        logging.info(f"Execution result:\n{result}")
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"请求处理错误: {str(e)}")
        return jsonify({'error': f'请求处理错误: {str(e)}'}), 500

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    app.run(debug=True, port=5000) 