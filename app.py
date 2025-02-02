from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.syslab_runner import SyslabExecutor
import logging
import traceback
from config import Config
import os

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(Config.LOG_PATH, 'middleware.log')
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route('/execute', methods=['POST'])
def execute():
    try:
        data = request.get_json()
        logger.info(f"Received request with data: {data}")
        
        if not data or 'code' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No code provided'
            }), 400
            
        code = data['code']
        logger.info(f"Executing code: {code}")
        
        # 执行代码
        result = SyslabExecutor.execute_code(code)
        logger.info(f"Execution result: {result}")
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'data': result['output']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500
            
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error processing request: {str(e)}\n{error_trace}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) 