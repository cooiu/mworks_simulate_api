import requests
import json
import sys
import os

def test_plot():
    base_url = "http://localhost:5000"
    session_id = "test_plot_session"
    
    # 创建会话
    print("创建会话...")
    response = requests.post(
        f"{base_url}/create_session",
        json={"session_id": session_id}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    
    if response.status_code != 200:
        print("创建会话失败")
        return
    
    # 执行绘图代码
    print("\n执行绘图代码...")
    plot_code = """
    # 清晰的绘图代码
    using TyPlot
    
    # 创建数据
    x = 0:(pi/100):(2*pi);
    y = sin.(x);
    
    # 显式创建图形
    figure()
    
    # 绘制图形
    plot(x, y, linewidth=2, color="blue")
    title("正弦波测试")
    xlabel("x")
    ylabel("sin(x)")
    grid(true)
    
    # 打印确认信息
    println("绘图命令已执行完成")
    """
    
    response = requests.post(
        f"{base_url}/execute",
        json={"session_id": session_id, "code": plot_code}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    # 打印文本输出
    print("\n文本输出:")
    for text in result.get('text', []):
        print(text)
    
    # 检查是否有图形
    if result.get('images'):
        print(f"\n成功生成了 {len(result['images'])} 个图形")
        
        # 保存图形
        for i, img in enumerate(result['images']):
            if img['type'] == 'svg':
                with open(f"test_plot_{i}.svg", "w", encoding="utf-8") as f:
                    f.write(img['data'])
                print(f"图形已保存为 test_plot_{i}.svg")
    else:
        print("\n没有生成图形")
        if result.get('error'):
            print(f"错误: {result['error']}")
    
    # 终止会话
    print("\n终止会话...")
    response = requests.post(
        f"{base_url}/terminate_session",
        json={"session_id": session_id}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

if __name__ == "__main__":
    test_plot() 