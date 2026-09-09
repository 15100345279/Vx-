import requests
import json
import datetime
import os

# ==================== 从环境变量读取配置 ====================
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
OPEN_ID = os.environ.get("OPEN_ID")
TEMPLATE_ID = os.environ.get("TEMPLATE_ID")
QWEATHER_API_KEY = os.environ.get("QWEATHER_KEY")      # 注意：Secrets 中名称是 QWEATHER_KEY
CITY = os.environ.get("CITY", "北京")                   # 如果未设置，默认北京

# ==================== 调试输出：确认配置是否读取成功 ====================
print("=" * 40)
print("🔍 当前配置信息（检查是否与 Secrets 一致）")
print(f"APP_ID:        {APP_ID}")
print(f"APP_SECRET:    {APP_SECRET[:6]}...{APP_SECRET[-4:] if APP_SECRET else ''}")  # 只显示部分
print(f"OPEN_ID:       {OPEN_ID}")
print(f"TEMPLATE_ID:   {TEMPLATE_ID}")
print(f"QWEATHER_KEY:  {QWEATHER_API_KEY[:8]}..." if QWEATHER_API_KEY else "未设置")
print(f"CITY:          {CITY}")
print("=" * 40)

# ==================== 1. 获取微信 access_token ====================
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        print(f"[微信] access_token 响应: {data}")
        if 'access_token' in data:
            return data['access_token']
        else:
            print(f"[微信] 获取 access_token 失败: {data.get('errmsg', '未知错误')}")
            return None
    except Exception as e:
        print(f"[微信] 请求 access_token 异常: {e}")
        return None

# ==================== 2. 获取天气数据（和风天气实时接口） ====================
def get_weather():
    url = "https://devapi.qweather.com/v7/weather/now"
    params = {
        "location": CITY,
        "key": QWEATHER_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        print(f"[天气] API 返回码: {data.get('code')}")
        print(f"[天气] 简要数据: {json.dumps(data, ensure_ascii=False)[:200]}...")
        
        if data.get('code') == '200':
            now = data['now']
            return {
                "city": CITY,
                "weather": now.get('text', '未知'),
                "temp": now.get('temp', '--')
            }
        else:
            print(f"[天气] 获取失败，完整返回: {data}")
            return None
    except Exception as e:
        print(f"[天气] 请求异常: {e}")
        return None

# ==================== 3. 组装并发送模板消息 ====================
def send_wechat_message(weather_data):
    if weather_data is None:
        print("[微信] 天气数据为空，取消发送")
        return False

    access_token = get_access_token()
    if not access_token:
        print("[微信] 无 access_token，取消发送")
        return False

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    
    # 消息体（字段必须和微信模板中的变量名完全一致）
    payload = {
        "touser": OPEN_ID,
        "template_id": TEMPLATE_ID,
        "data": {
            "city": {"value": weather_data['city']},
            "weather": {"value": weather_data['weather']},
            "temp": {"value": f"{weather_data['temp']}℃"},
            "uv_index": {"value": "中等"},     # 如果需要真实紫外线，可额外调用指数接口
            "tips": {"value": "今天天气不错，注意防晒！"}
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        print(f"[微信] 发送结果: {result}")
        
        if result.get('errcode') == 0:
            print("[微信] ✅ 推送成功！")
            return True
        else:
            print(f"[微信] ❌ 推送失败: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"[微信] 发送请求异常: {e}")
        return False

# ==================== 4. 主程序入口 ====================
if __name__ == "__main__":
    print("\n🚀 开始执行天气推送任务...")
    weather = get_weather()
    if weather:
        print(f"[天气] 当前 {weather['city']}：{weather['weather']}，{weather['temp']}℃")
    success = send_wechat_message(weather)
    print(f"\n🏁 任务结束，{'成功' if success else '失败'}")
