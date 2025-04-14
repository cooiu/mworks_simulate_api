import requests
import json
import base64
import os
import time
import uuid
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_session_api():
    base_url = "http://localhost:5000"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    
    print(f"\n=== 开始测试会话 {session_id} ===")
    
    try:
        # 1. 创建新会话
        print("\n1. 创建新会话...")
        response = requests.post(
            f"{base_url}/create_session",
            json={"session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        if response.status_code != 200:
            print("创建会话失败，终止测试")
            return
            
        # 2. 执行第一段代码：生成数据并绘图
        print("\n2. 执行第一段代码：生成数据并绘图...")
        code1 = """# 生成测试数据
using TyPlot

# 生成数据
x = 0:(pi/100):(2*pi);
y1 = sin.(x);
y2 = cos.(x);
println("数据已生成")

# 明确创建图形
figure()  # 创建新图形
plot(x, y1)  # 绘制正弦曲线
title("正弦波")  # 添加标题
xlabel("x")  # x轴标签
ylabel("sin(x)")  # y轴标签
grid(true)  # 显示网格
println("图形已创建") 
"""
        response = requests.post(
            f"{base_url}/execute",
            json={
                "session_id": session_id,
                "code": code1
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        # 打印文本输出
        print("\n文本输出:")
        for text in result.get('text', []):
            print(text)
        
        # 处理图片输出
        print("\n图片输出:")
        for i, image in enumerate(result.get('images', [])):
            img_data = image['data']
            img_filename = f"test_output_image_{session_id}_{i}.svg"
            with open(img_filename, 'w', encoding='utf-8') as f:
                f.write(img_data)
            print(f"图片已保存为: {img_filename}")
        
        # 3. 执行第二段代码：使用之前定义的变量
        print("\n3. 执行第二段代码：使用之前定义的变量...")
        code2 = """# 使用之前定义的变量进行新的计算
println("变量y1的前几个值: ", y1[1:5])
println("变量类型: ", typeof(y1))
println("x 的长度: ", length(x))
println("y1 的长度: ", length(y1))

# 创建新的图形，确保使用figure()显式创建
figure()  # 创建新图形窗口
plot(x, y2, linewidth=2, color="red")
title("余弦波信号")
xlabel("x")
ylabel("cos(x)")
println("新图形已创建")
"""
        response = requests.post(
            f"{base_url}/execute",
            json={
                "session_id": session_id,
                "code": code2
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        # 打印文本输出
        print("\n文本输出:")
        for text in result.get('text', []):
            print(text)
        
        # 处理图片输出
        print("\n图片输出:")
        for i, image in enumerate(result.get('images', [])):
            img_data = image['data']
            img_filename = f"test_output_image_{session_id}_2_{i}.svg"
            with open(img_filename, 'w', encoding='utf-8') as f:
                f.write(img_data)
            print(f"图片已保存为: {img_filename}")
        
        # 4. 终止会话
        print("\n4. 终止会话...")
        response = requests.post(
            f"{base_url}/terminate_session",
            json={"session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print(f"\n=== 会话 {session_id} 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        
        # 确保会话被终止
        try:
            requests.post(
                f"{base_url}/terminate_session",
                json={"session_id": session_id},
                headers={"Content-Type": "application/json"}
            )
        except:
            pass 

def test_multiple_sessions():
    """测试多个并发会话"""
    base_url = "http://localhost:5000"
    session_ids = [f"test_session_{uuid.uuid4().hex[:8]}" for _ in range(3)]
    
    print("\n=== 开始测试多个并发会话 ===")
    
    try:
        # 创建多个会话
        for session_id in session_ids:
            print(f"\n创建会话 {session_id}...")
            response = requests.post(
                f"{base_url}/create_session",
                json={"session_id": session_id},
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
            
            if response.status_code == 200:
                # 在每个会话中执行简单的代码
                code = f"""# 测试图形输出
using TyPlot
x = 0:(pi/100):(2*pi);
y = sin.(x);

# 创建图形
figure()
plot(x, y)
title("会话 {session_id} 的测试图形")
println("这是会话 {session_id} 的输出")
"""
                response = requests.post(
                    f"{base_url}/execute",
                    json={
                        "session_id": session_id,
                        "code": code
                    },
                    headers={"Content-Type": "application/json"}
                )
                print(f"执行结果: {response.json()}")
        
        # 等待一会儿
        time.sleep(2)
        
        # 终止所有会话
        for session_id in session_ids:
            print(f"\n终止会话 {session_id}...")
            response = requests.post(
                f"{base_url}/terminate_session",
                json={"session_id": session_id},
                headers={"Content-Type": "application/json"}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        
        print("\n=== 多会话测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())
        
        # 确保所有会话被终止
        for session_id in session_ids:
            try:
                requests.post(
                    f"{base_url}/terminate_session",
                    json={"session_id": session_id},
                    headers={"Content-Type": "application/json"}
                )
            except:
                pass

if __name__ == "__main__":
    print("=== 开始API测试 ===")
    
    # 测试单个会话
    test_session_api()
    
    # # 测试多个并发会话
    # test_multiple_sessions()
    
    print("\n=== API测试完成 ===")

