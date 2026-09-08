import requests
import json
import datetime

# --- 1. 配置信息（全部替换成你自己的）---
APP_ID = "wx0eabf1435f9f1952"
APP_SECRET = "fa316339631f13f499ea4fb3f0c7414e"
OPEN_ID = "oAa6628IU8QnT7zqoROPHWWMs1Jc"  # 从用户列表复制的那一串
TEMPLATE_ID = "e-_wpDhzSwvRDFJ_H1kT01bzgcGchbjrzGvir3TSSv8"  # 从模板消息接口获取的ID

# 和风天气配置
CITY = "北京"  # 改成你的城市
QWEATHER_API_KEY = "ef8615cbc29e4f258a67a528d0398252"  # 下面会教你怎么获取

# --- 2. 获取微信 access_token ---
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    response = requests.get(url).json()
    # 注意：实际使用时应加入错误处理
    return response['access_token']

# --- 3. 获取天气数据（以和风天气为例）---
def get_weather():
    # 使用实时天气接口[reference:15]
    url = "https://devapi.qweather.com/v7/weather/now"
    params = {
        "location": CITY,
        "key": QWEATHER_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    # 假设接口返回成功，解析数据
    if data['code'] == '200':
        now = data['now']
        return {
            "city": CITY,
            "weather": now['text'],
            "temp": now['temp']
            # 注意：和风天气免费版实时接口可能不直接返回紫外线指数
            # 如需紫外线指数，可使用 "https://devapi.qweather.com/v7/indices/1d" 接口
            # 这里为演示，我们手动设置一个
        }
    else:
        print("获取天气失败")
        return None

# --- 4. 组装并发送模板消息 ---
def send_wechat_message(weather_data):
    if weather_data is None:
        return

    access_token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

    # 构造消息体，必须和你在微信后台定义的模板变量完全一致
    data = {
        "touser": OPEN_ID,
        "template_id": TEMPLATE_ID,
        "data": {
            "city": {"value": weather_data['city']},
            "weather": {"value": weather_data['weather']},
            "temp": {"value": f"{weather_data['temp']}℃"},
            # 模拟紫外线指数，实际可以从其他API获取
            "uv_index": {"value": "中等"},
            "tips": {"value": "今天天气不错，注意防晒！"}
        }
    }

    response = requests.post(url, json=data)
    print(response.json())

# --- 5. 主程序入口 ---
if __name__ == "__main__":
    weather = get_weather()
    send_wechat_message(weather)