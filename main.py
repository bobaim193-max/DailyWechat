from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage
import os
import json
from datetime import datetime, timedelta
import requests

nowtime = datetime.utcnow() + timedelta(hours=8)
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d")


def get_time():
    dictDate = {'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三', 'Thursday': '星期四',
                'Friday': '星期五', 'Saturday': '星期六', 'Sunday': '星期天'}
    a = dictDate[nowtime.strftime('%A')]
    return nowtime.strftime("%Y年%m月%d日") + a


def get_words():
    # 保持之前修复的逻辑，防止接口报错
    return "不管天气如何，记得带上自己的阳光！"

def get_weather(city, key):
    # 增加异常处理，防止天气接口偶尔抽风导致程序崩溃
    try:
        url = f"https://api.seniverse.com/v3/weather/daily.json?key={key}&location={city}&language=zh-Hans&unit=c&start=-1&days=5"
        res = requests.get(url).json()
        print(res)
        weather = (res['results'][0])["daily"][0]
        city_name = (res['results'][0])["location"]["name"]
        return city_name, weather
    except Exception as e:
        print(f"天气获取失败: {e}")
        return city, {'text_day': '未知', 'high': '-', 'low': '-', 'wind_direction': '未知'}

def get_count(born_date):
    # 这个函数非常通用，也可以用来计算“在一起”的天数
    delta = today - datetime.strptime(born_date, "%Y-%m-%d")
    return delta.days


def get_birthday(birthday):
    nextdate = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
    if nextdate < today:
        nextdate = nextdate.replace(year=nextdate.year + 1)
    return (nextdate - today).days


if __name__ == '__main__':
    app_id = os.getenv("APP_ID")
    app_secret = os.getenv("APP_SECRET")
    template_id = os.getenv("TEMPLATE_ID")
    weather_key = os.getenv("WEATHER_API_KEY")

    client = WeChatClient(app_id, app_secret)
    wm = WeChatMessage(client)

    f = open("users_info.json", encoding="utf-8")
    js_text = json.load(f)
    f.close()
    data = js_text['data']
    num = 0
    words = get_words()
    out_time = get_time()

    print(words, out_time)

    for user_info in data:
        born_date = user_info['born_date']
        birthday = born_date[5:]
        city = user_info['city']
        user_id = user_info['user_id']
        name = user_info['user_name'].upper()
        
        # --- 修改点1：获取在一起的起始日期 ---
        # 对应你在 users_info.json 里加的 "days": "2023-10-20"
        love_start_date = user_info['days'] 
        
        wea_city, weather = get_weather(city, weather_key)
        
        # 为了避免混淆，建议这里新建一个字典用来发包
        data_packet = dict()
        data_packet['time'] = {'value': out_time}
        data_packet['words'] = {'value': words}
        data_packet['weather'] = {'value': weather['text_day']}
        data_packet['city'] = {'value': wea_city}
        data_packet['tem_high'] = {'value': weather['high']}
        data_packet['tem_low'] = {'value': weather['low']}
        data_packet['born_days'] = {'value': get_count(born_date)}
        data_packet['birthday_left'] = {'value': get_birthday(birthday)}
        data_packet['wind'] = {'value': weather['wind_direction']}
        data_packet['name'] = {'value': name}
        
        # --- 修改点2：计算并添加在一起的天数 ---
        # 直接复用 get_count 函数，它能计算当前日期与过去某日期的差值
        data_packet['love_days'] = {'value': get_count(love_start_date)}

        # 注意：这里发送的是 data_packet
        res = wm.send_template(user_id, template_id, data_packet)
        print(res)
        num += 1
    print(f"成功发送{num}条信息")
