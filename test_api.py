import requests
import json
import base64
import os

def test_api():
    url = "http://localhost:5000/execute"
    
    # 测试代码 - 注意这里使用三引号时不要有缩进
    code = """# 生成测试数据
x = collect(0:0.1:2π)
y1 = sin.(x)
y2 = cos.(x)

println("数据已生成")

# 创建新图形
using TyPlot
using TyDSPSystem

sine1 = dsp_SineWave(Amplitude=2,Frequency=10,SamplesPerFrame=1000)
y1 = step(sine1)
plot(y1)
hold()
println("生成图形")

# 计算一些统计值
println("\\n统计信息:")
println("sin(x) 最大值: ", maximum(y1))
println("sin(x) 最小值: ", minimum(y1))
println("cos(x) 最大值: ", maximum(y2))
println("cos(x) 最小值: ", minimum(y2))"""
    
    try:
        print("发送请求...")
        response = requests.post(
            url,
            json={"code": code},
            headers={"Content-Type": "application/json"}
        )
        
        print("\nStatus Code:", response.status_code)
        
        if response.status_code == 200:
            result = response.json()
            
            # 打印文本输出
            print("\n文本输出:")
            for text in result.get('text', []):
                print(text)
            
            # 处理图片输出
            print("\n图片输出:")
            for i, image in enumerate(result.get('images', [])):
                # 从base64字符串中提取实际的图片数据
                img_data = image['data'].split(',')[1]
                # 保存为文件以便查看
                img_filename = f"test_output_image_{i}.png"
                with open(img_filename, 'wb') as f:
                    f.write(base64.b64decode(img_data))
                print(f"图片已保存为: {img_filename}")
            
            # 检查错误
            if result.get('error'):
                print("\n执行错误:")
                print(result['error'])
                
        else:
            print("\n错误响应:")
            print(response.text)
                
    except Exception as e:
        print(f"请求错误: {str(e)}")
        import traceback
        print("详细错误信息:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_api() 