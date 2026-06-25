import os
os.environ['TZ'] = 'Asia/Shanghai'

from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime
import time

app = Flask(__name__)

# 存储最新环境数据
latest_env = {
    "feel": "还没收到数据",
    "temp": "--",
    "weather": "--",
    "updated_at": "--",
    "battery": "--"
}

@app.route('/upload', methods=['POST'])
def upload():
    global latest_env
    
    try:
        # 接收手机上报的数据
        data = request.get_json()
        print(f"收到手机数据: {data}")
        
        # 提取经纬度（兼容不同格式）
        lat = data.get('lat') or data.get('latitude') or 31.23
        lon = data.get('lon') or data.get('longitude') or 121.47
        
        # 提取电量
        battery = data.get('battery_level') or data.get('battery') or data.get('Battery')
        
        # 查天气（用wttr.in）
        weather_url = f"https://wttr.in/{lat},{lon}?format=j1"
        weather_resp = requests.get(weather_url, timeout=10)
        weather_data = weather_resp.json()
        
        # 解析天气
        current = weather_data['current_condition'][0]
        temp = current['temp_C']
        humidity = current['humidity']
        weather_desc = current['weatherDesc'][0]['value']
        
        # 翻译体感（更生动的版本）
        # 天气描述翻译
        weather_cn = {
            "Sunny": "晴天",
            "Partly cloudy": "多云转晴",
            "Cloudy": "阴天",
            "Overcast": "阴天",
            "Mist": "薄雾",
            "Fog": "雾天",
            "Rain": "下雨",
            "Light rain": "小雨",
            "Heavy rain": "大雨",
            "Snow": "下雪",
            "Thunderstorm": "雷阵雨"
        }
        weather_text = weather_cn.get(weather_desc, weather_desc)
        
        # 体感温度描述
        temp_int = int(temp)
        if temp_int >= 35:
            feel_temp = "热得发烫"
        elif temp_int >= 30:
            feel_temp = "有点热"
        elif temp_int >= 25:
            feel_temp = "温暖舒适"
        elif temp_int >= 20:
            feel_temp = "凉爽宜人"
        elif temp_int >= 10:
            feel_temp = "有点凉"
        elif temp_int >= 0:
            feel_temp = "挺冷的"
        else:
            feel_temp = "冻得发抖"
        
        # 组装体感句
        feel = f"现在外面{weather_text}，{temp}度，{feel_temp}，湿度{humidity}%"
        
        # 如果有电量信息
        if battery:
            try:
                battery_int = int(battery)
                if battery_int < 20:
                    feel += f"，手机电量只剩{battery_int}%，该充电了"
                else:
                    feel += f"，手机电量{battery_int}%"
            except:
                feel += f"，手机电量{battery}%"
        
        # 保存到内存
        latest_env = {
            "feel": feel,
            "temp": temp,
            "weather": weather_desc,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "battery": str(battery) if battery else "--"
        }
        
        return jsonify({"status": "ok", "feel": feel})
        
    except Exception as e:
        print(f"出错了: {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/get_env', methods=['GET'])
def get_env():
    return jsonify(latest_env)

@app.route('/', methods=['GET'])
def home():
    return f"""
    <h1>🌤️ 环境感知服务运行中</h1>
    <p><strong>最新环境：</strong>{latest_env['feel']}</p>
    <p><strong>更新时间：</strong>{latest_env['updated_at']}</p>
    <p><strong>手机电量：</strong>{latest_env['battery']}%</p>
    <hr>
    <p>📱 手机POST数据到 /upload</p>
    <p>🤖 Claude GET /get_env</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
