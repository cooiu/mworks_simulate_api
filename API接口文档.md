# SysLab中间件接口文档

## 一、环境配置

### 1. 系统要求
- Python 3.8+
- Julia 1.9.3
- TongYuan相关Julia包环境

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置
可通过.env文件或系统环境变量配置以下参数：
- JULIA_PATH: Julia可执行文件路径（默认：C:\Users\Public\TongYuan\julia-1.9.3\bin\julia.exe）
- LOG_PATH: 日志文件路径（默认：C:\Users\Public\TongYuan\logs）
- TEMP_DIR: 临时文件目录（默认：项目根目录下的temp文件夹）

### 4. Julia环境初始化
在首次使用前，需要初始化Julia环境并安装必要的包：
```bash
python init_julia.py
```

## 二、接口说明

### 1. 代码执行接口

- **URL**: `/execute`
- **方法**: POST
- **Content-Type**: application/json

#### 请求参数
```json
{
    "code": "Julia代码内容"
}
```

#### 返回结果
```json
{
    "images": [
        {
            "type": "svg",
            "data": "SVG图像内容"
        }
    ],
    "text": ["输出文本行1", "输出文本行2", ...],
    "error": "错误信息（如有）"
}
```

### 2. 使用示例

#### Python请求示例
```python
import requests

url = "http://localhost:5000/execute"
code = """
using TyPlot

x = collect(0:0.1:2π)
y = sin.(x)
plot(x, y)
title("正弦波")
xlabel("x")
ylabel("sin(x)")
"""

response = requests.post(
    url,
    json={"code": code},
    headers={"Content-Type": "application/json"}
)

result = response.json()
print(result)
```

## 三、使用注意事项

1. 执行Julia代码时，以下包会自动加载：
   - TyPlot
   - TyBase
   - TyMath
   - PyCall

2. 若需使用其他Julia包，代码中应包含using或import语句，系统会自动安装

3. 图形绘制：
   - 使用TyPlot包进行绘图
   - 图形将自动保存并以SVG格式返回

4. 错误处理：
   - Julia运行错误将在返回结果的error字段中显示
   - 系统错误将返回HTTP 500错误

## 四、启动服务器

```bash
python main.py
```
服务器默认在5000端口启动，可通过浏览器访问 http://localhost:5000 