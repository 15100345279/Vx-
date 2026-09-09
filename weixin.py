import requests
import json
import os

# ==================== 从环境变量读取配置 ====================
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
TEMPLATE_ID = os.environ.get("TEMPLATE_ID")
QWEATHER_API_KEY = os.environ.get("QWEATHER_KEY")

# USERS 是一个 JSON 数组，格式：[{"name":"张三","openid":"oAa...","city":"北京"}, ...]
USERS_JSON = '[{"name":"自己","openid":"oAa6628IU8QnT7zqoROPHWWMs1Jc","city":"北京"}]'
try:
    USERS = json.loads(USERS_JSON)
except Exception as e:
    print(f"❌ USERS 环境变量 JSON 解析失败: {e}")
    USERS = []

print("=" * 50)
print("📋 当前配置信息")
print(f"APP_ID:        {APP_ID}")
print(f"TEMPLATE_ID:   {TEMPLATE_ID}")
print(f"QWEATHER_KEY:  {QWEATHER_API_KEY[:8] if QWEATHER_API_KEY else '未设置'}...")
print(f"用户数量:      {len(USERS)}")
for i, u in enumerate(USERS, 1):
    print(f"  {i}. {u.get('name', '未命名')} -> {u.get('city', '未设置')}")
print("=" * 50)

# ==================== 1. 获取微信 access_token ====================
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if 'access_token' in data:
            print("[微信] ✅ access_token 获取成功")
            return data['access_token']
        else:
            print(f"[微信] ❌ access_token 获取失败: {data}")
            return None
    except Exception as e:
        print(f"[微信] ❌ access_token 请求异常: {e}")
        return None

# ==================== 2. 获取单个城市的天气（和风天气） ====================
def get_weather(city):
    # 使用正式版 API（不要用 devapi）
    url = "https://devapi.qweather.com/v7/weather/now"
    params = {
        "location": city,
        "key": QWEATHER_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        code = data.get('code')
        print(f"[天气] {city} 返回码: {code}")
        if code == '200':
            now = data['now']
            return {
                "city": city,
                "weather": now.get('text', '未知'),
                "temp": now.get('temp', '--')
            }
        else:
            print(f"[天气] ❌ {city} 获取失败: {data}")
            return None
    except Exception as e:
        print(f"[天气] ❌ {city} 请求异常: {e}")
        return None

# ==================== 3. 发送模板消息给单个用户 ====================
def send_to_user(open_id, weather_data, user_name="用户"):
    if weather_data is None:
        print(f"[微信] ⚠️ {user_name} 天气数据为空，跳过发送")
        return False

    access_token = get_access_token()
    if not access_token:
        return False

    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    
    payload = {
        "touser": open_id,
        "template_id": TEMPLATE_ID,
        "data": {
            "city": {"value": weather_data['city']},
            "weather": {"value": weather_data['weather']},
            "temp": {"value": f"{weather_data['temp']}℃"},
            "uv_index": {"value": "中等"},      # 如需真实紫外线，可额外调用指数接口
            "tips": {"value": "今天天气不错，注意防晒！"}
        }
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            print(f"[微信] ✅ {user_name} 推送成功")
        else:
            print(f"[微信] ❌ {user_name} 推送失败: {result}")
        return result.get('errcode') == 0
    except Exception as e:
        print(f"[微信] ❌ {user_name} 发送异常: {e}")
        return False

# ==================== 4. 主程序 ====================
if __name__ == "__main__":
    print("\n🚀 开始多用户天气推送任务...")
    success_count = 0
    total = len(USERS)
    
    if total == 0:
        print("⚠️ 没有用户配置，请检查 USERS 环境变量")
        exit(0)
    
    for idx, user in enumerate(USERS, 1):
        name = user.get('name', f"用户{idx}")
        open_id = user.get('openid')
        city = user.get('city')
        
        if not open_id or not city:
            print(f"[系统] ⚠️ {name} 配置不完整（openid或city缺失），跳过")
            continue
        
        print(f"\n--- 处理 {idx}/{total}：{name}（{city}） ---")
        weather = get_weather(city)
        if send_to_user(open_id, weather, name):
            success_count += 1
    
    print(f"\n🏁 任务结束，成功推送 {success_count}/{total} 人")
