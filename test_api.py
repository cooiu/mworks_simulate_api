import requests
import json
import traceback

def test_api():
    url = "http://localhost:5000/execute"
    
    # 使用更完整的绘图功能
    code = """
    # 生成测试数据
    x = collect(0:0.1:2π)
    y1 = sin.(x)
    y2 = cos.(x)
    
    println("数据已生成")
    
    # 创建新图形
    using TyPlot
    figure()
    
    # 绘制多条曲线
    plot(x, y1, "b-", label="sin(x)")
    plot(x, y2, "r--", label="cos(x)")
    
    # 添加网格
    grid("on")
    
    # 添加标签
    xlabel("x")
    ylabel("y")
    
    # 保存图形
    savefig("trig_functions.syslabfig")
    println("图形已保存")
    
    # 计算一些统计值
    println("\\n统计信息:")
    println("sin(x) 最大值: ", maximum(y1))
    println("sin(x) 最小值: ", minimum(y1))
    println("cos(x) 最大值: ", maximum(y2))
    println("cos(x) 最小值: ", minimum(y2))
    """
    
    try:
        print("发送请求...")
        response = requests.post(
            url,
            json={"code": code},
            headers={"Content-Type": "application/json"}
        )
        
        print("\nStatus Code:", response.status_code)
        print("\n完整响应:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result = response.json()
            
            if result["status"] == "success":
                print("\n执行输出:")
                print(result["data"])
                
                # 检查图片
                import os
                temp_dir = os.path.join(os.getcwd(), "temp")
                fig_file = os.path.join(temp_dir, "trig_functions.syslabfig")
                if os.path.exists(fig_file):
                    print(f"\n成功生成图片: {fig_file}")
                    # 获取文件大小
                    size = os.path.getsize(fig_file)
                    print(f"文件大小: {size/1024:.2f} KB")
                else:
                    print("\n未找到生成的图片")
        else:
            print("\n错误响应:")
            print(response.text)
                
    except Exception as e:
        print("请求错误:", str(e))
        print("详细错误信息:", traceback.format_exc())

if __name__ == "__main__":
    test_api() 