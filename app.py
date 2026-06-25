from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# 存储最新环境数据
latest_env = {
    "feel": "还没收到数据",
    "temp": "--",
    "weather": "--",
    "updated_at": "--"
}

@app.route('/upload', methods=['POST'])
def upload():
    global latest_env
    
    try:
        # 接收手机上报的数据
        data = request.get_json()
        print(f"收到手机数据: {data}")
        
        # 提取经纬度
        lat = data.get('lat') or data.get('latitude') or 31.23
        lon = data.get('lon') or data.get('longitude') or 121.47
        
        # 查天气
        weather_url = f"https://wttr.in/{lat},{lon}?format=j1"
        weather_resp = requests.get(weather_url, timeout=10)
        weather_data = weather_resp.json()
        
        # 解析天气
        current = weather_data['current_condition'][0]
        temp = current['temp_C']
        humidity = current['humidity']
        weather_desc = current['weatherDesc'][0]['value']
        
        # 翻译体感
        feel = f"现在外面{weather_desc}，{temp}度，湿度{humidity}%"
        
        # 如果有电量信息
        battery = data.get('battery_level')
        if battery:
            feel += f"，手机电量{battery}%"
        
        # 保存
        latest_env = {
            "feel": feel,
            "temp": temp,
            "weather": weather_desc,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    <h1>环境感知服务运行中</h1>
    <p>最新环境：{latest_env['feel']}</p>
    <p>更新时间：{latest_env['updated_at']}</p>
    <p>手机POST数据到 /upload，Claude GET /get_env</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
