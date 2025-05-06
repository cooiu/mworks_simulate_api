from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from utils.syslab_runner import SyslabExecutor

app = Flask(__name__)
# 更新CORS配置，允许多个源访问
CORS(app)

@app.route('/create_session', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': '没有提供会话ID'}), 400

        logging.info(f"Creating new session: {session_id}")
        result = SyslabExecutor.create_session(session_id)
        
        if 'error' in result:
            return jsonify(result), 400
            
        return jsonify(result)

    except Exception as e:
        logging.error(f"创建会话错误: {str(e)}")
        return jsonify({'error': f'创建会话错误: {str(e)}'}), 500

@app.route('/execute', methods=['POST'])
def execute_code():
    try:
        data = request.get_json()
        code = data.get('code')
        session_id = data.get('session_id')
        
        if not code:
            return jsonify({'error': '没有提供代码'}), 400

        logging.info(f"Received code execution request for session: {session_id}")
        logging.info(f"Code:\n{code}")
        
        # 使用 SyslabExecutor 执行代码
        result = SyslabExecutor.execute_code(code, session_id)
        
        logging.info(f"Execution result:\n{result}")
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"请求处理错误: {str(e)}")
        return jsonify({'error': f'请求处理错误: {str(e)}'}), 500

@app.route('/terminate_session', methods=['POST'])
def terminate_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': '没有提供会话ID'}), 400

        logging.info(f"Terminating session: {session_id}")
        result = SyslabExecutor.terminate_session(session_id)
        
        if 'error' in result:
            return jsonify(result), 400
            
        return jsonify(result)

    except Exception as e:
        logging.error(f"终止会话错误: {str(e)}")
        return jsonify({'error': f'终止会话错误: {str(e)}'}), 500

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    app.run(host='0.0.0.0', debug=True, port=5000) 