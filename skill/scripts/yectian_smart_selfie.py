#!/usr/bin/env python3
"""
野甜智能自拍 - 根据上海时间+天气生成场景
"""
import json
import os
import sys
import base64
import subprocess
from datetime import datetime
import pytz

# 配置
CONFIG_PATH = os.path.expanduser("~/.openclaw/config/jimeng/config.json")
REFERENCE_IMAGE = os.path.expanduser("~/.openclaw/workspace/clawra/skill/assets/clawra.jpg")

# 固定的相似度提示词
IDENTITY_PROMPT = (
    "identical person, same face identity, face consistency locked, "
    "MALE person only, MUST be male guy man, "
    "【AGE】: mature face around 25 years old, youthful but mature features, NOT young-looking, "
    "【FACE SHAPE】: oval face or heart-shaped face, pointed chin, smooth cheekbone lines, mature male proportions, "
    "【EYES】: deep-set eyes, clear double eyelids, lively sparkling eyes with life, expressive, charming gaze, NOT dull eyes, "
    "【NOSE】: straight and tall nasal bridge, round and delicate nose tip, narrow nostrils, "
    "【LIPS】: full lips with clear Cupid's bow outline, healthy light pink color, "
    "【JAWLINE】: sharp and defined jawline, obvious bone structure, male jawline, "
    "【SKIN TONE】: fair porcelain skin with healthy natural glow, even skin tone, "
    "【HAIR】: medium-short hair, shoulder-length hair, between short and medium-long, dark brown or black color, same hair length as reference photo, NEVER very short pixie hair, NEVER long hair, "
    "【HAIRLINE】: consistent with reference, same hairline shape, "
    "【BEARD】: clean shaved, NO beard at all, completely clean face, stubble-free, NEVER facial hair, "
    "【SKIN TEXTURE】: delicate and smooth skin texture, nearly invisible pores, fine and smooth, "
    "【OVERALL VIBE】: fresh youthful male aesthetic, around 25 years old, handsome guy with lively spirit, "
    "identity consistency priority is the HIGHEST, "
    "face must remain completely consistent (90%+ similarity), "
    "high realistic photography style, detailed skin texture, realistic lighting, natural look, "
    "forbidden: female, forbidden: very short hair, forbidden: pixie cut, forbidden: long hair, forbidden: beard, forbidden: stubble, "
    "forbidden: changing facial features, forbidden: changing skin tone, forbidden: person deformation, "
    "forbidden: younger face, forbidden: dull expression"
)

def get_shanghai_time():
    """获取上海当前时间"""
    tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(tz)

def get_shanghai_weather():
    """获取上海天气"""
    try:
        result = subprocess.run(
            ['curl', '-s', 'wttr.in/Shanghai?format=j1'],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        w = data['current_condition'][0]
        return {
            'weather': w['weatherDesc'][0]['value'].lower(),
            'temp': int(w['temp_C']),
            'feels': int(w['FeelsLikeC']),
            'humidity': int(w['humidity']),
            'precip': float(w['precipMM'])
        }
    except Exception as e:
        print(f"获取天气失败: {e}")
        return {'weather': 'clear', 'temp': 20, 'feels': 20, 'humidity': 50, 'precip': 0}

def get_time_period(hour):
    """根据小时判断时间段"""
    if 5 <= hour < 7:
        return 'early_morning'
    elif 7 <= hour < 9:
        return 'morning'
    elif 9 <= hour < 12:
        return 'work_morning'
    elif 12 <= hour < 14:
        return 'noon'
    elif 14 <= hour < 18:
        return 'work_afternoon'
    elif 18 <= hour < 21:
        return 'evening'
    else:
        return 'night'

def generate_context_scenario(time_period, weather, temp):
    """根据时间段+天气生成场景"""
    
    # 天气因素
    weather_factors = {
        'clear': 'sunny, bright natural lighting, blue sky',
        'sunny': 'sunny, bright natural lighting, golden hour glow',
        'cloudy': 'overcast, soft diffused lighting, cloudy sky',
        'rain': 'rainy, rain drops on window, wet atmosphere, moody lighting',
        'fog': 'foggy, misty atmosphere, soft ethereal lighting',
        'snow': 'snowy, cold atmosphere, white winter scenery',
        'storm': 'stormy, dramatic lighting, dark clouds'
    }
    
    weather_desc = weather_factors.get(weather, weather_factors['clear'])
    
    # 时间段场景
    scenarios = {
        'early_morning': {
            'scene': 'bathroom bedroom, fresh morning light from window',
            'action': 'just woke up, casual morning pose, fresh face',
            'outfit': 'casual home wear, loose white t-shirt',
            'lighting': 'soft morning sunlight, warm tone'
        },
        'morning': {
            'scene': 'outdoor street, morning exercise, park',
            'action': 'casual walk or light exercise, energetic pose',
            'outfit': 'sports wear, athletic hoodie, comfortable',
            'lighting': 'bright morning sun, fresh air atmosphere'
        },
        'work_morning': {
            'scene': 'modern office interior, coffee shop, co-working space',
            'action': 'professional working pose, holding coffee cup, looking at camera',
            'outfit': 'smart casual or business casual, shirt, clean and tidy',
            'lighting': 'indoor professional lighting, window light'
        },
        'noon': {
            'scene': 'restaurant cafe, lunch break',
            'action': 'relaxed lunch pose, enjoying meal or coffee',
            'outfit': 'casual smart, polo shirt or casual shirt',
            'lighting': 'natural midday light from windows'
        },
        'work_afternoon': {
            'scene': 'office desk area, modern workplace',
            'action': 'working pose, typing or using phone, thoughtful expression',
            'outfit': 'business casual, shirt with sleeves rolled up',
            'lighting': 'afternoon indoor lighting, desk lamp glow'
        },
        'evening': {
            'scene': 'rooftop bar, city skyline, outdoor lounge',
            'action': 'relaxed evening pose, leaning or standing, city lights background',
            'outfit': 'smart casual, jacket or stylish top, evening out',
            'lighting': 'golden hour sunset, warm city lights, romantic atmosphere'
        },
        'night': {
            'scene': 'home living room, late evening relaxation',
            'action': 'casual relaxed pose, lounging, peaceful expression',
            'outfit': 'home casual, comfortable hoodie or casual shirt',
            'lighting': 'warm indoor lighting, lamp light, cozy atmosphere'
        }
    }
    
    scenario = scenarios.get(time_period, scenarios['work_afternoon'])
    
    # 雨天额外元素
    rain_elements = ""
    if weather in ['rain', 'rainy'] or scenario.get('precip', 0) > 0:
        rain_elements = ", rain drops on glass, wet city lights reflection, umbrella nearby"
    
    # 温度因素
    temp_elements = ""
    if temp < 10:
        temp_elements = ", winter cold atmosphere, breath visible in air"
    elif temp > 30:
        temp_elements = ", hot summer feeling, sweat on skin"
    
    # 组合场景描述
    full_scene = f"{scenario['scene']}, {weather_desc}, {scenario['lighting']}{rain_elements}{temp_elements}"
    full_action = f"{scenario['action']}, {scenario['outfit']}"
    
    return full_scene, full_action

def build_prompt(time_period, weather, temp, user_request=""):
    """构建完整提示词"""
    scene, action = generate_context_scenario(time_period, weather, temp)
    
    prompt_parts = []
    
    if "selfie" in user_request.lower() or "mirror" in user_request.lower():
        prompt_parts.append("selfie photo, mirror selfie")
    else:
        prompt_parts.append("portrait photo")
    
    prompt_parts.append(action)
    prompt_parts.append(f"environment: {scene}")
    prompt_parts.append(f"expression: natural smiling face, genuine smile")
    prompt_parts.append(IDENTITY_PROMPT)
    
    return ", ".join(prompt_parts)

def main():
    # 获取时间和天气
    now = get_shanghai_time()
    weather = get_shanghai_weather()
    time_period = get_time_period(now.hour)
    
    print(f"📍 上海时间: {now.strftime('%H:%M')} ({now.strftime('%Y-%m-%d')})")
    print(f"🌤️  天气: {weather['weather']}, 温度: {weather['temp']}°C")
    print(f"⏰ 时段: {time_period}")
    print()
    
    # 如果有用户输入，显示建议的场景
    if len(sys.argv) > 1:
        user_request = sys.argv[1]
        print(f"用户请求: {user_request}")
        print()
    
    # 显示建议场景
    scene, action = generate_context_scenario(time_period, weather['weather'], weather['temp'])
    print(f"📸 建议场景: {scene}")
    print(f"👔 建议动作/穿搭: {action}")
    print()
    
    # 构建提示词
    prompt = build_prompt(time_period, weather['weather'], weather['temp'], user_request if len(sys.argv) > 1 else "")
    print(f"完整提示词:\n{prompt}")
    
    # 生成图片
    from volcengine.visual.VisualService import VisualService
    config = json.load(open(CONFIG_PATH))
    service = VisualService()
    service.set_ak(config["access_key_id"])
    service.set_sk(config["secret_key"])
    
    with open(REFERENCE_IMAGE, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    print("\n正在生成图片...")
    
    body = {
        "req_key": "jimeng_t2i_v40",
        "prompt": prompt,
        "image_base64": img_base64,
        "size": 4194304,
        "force_single": True
    }
    
    result = service.cv_process(body)
    
    if result.get("code") == 10000:
        b64 = result['data'].get('binary_data_base64', [])
        if b64:
            filepath = f"/tmp/smart_selfie_{os.getpid()}.jpg"
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(b64[0]))
            print(f"\n✅ 生成成功: {filepath}")
            print("\n[OUTPUT_JSON]")
            print(json.dumps({
                "success": True,
                "file": filepath,
                "time_period": time_period,
                "weather": weather,
                "prompt": prompt
            }))
        else:
            print("\n❌ 生成失败: 未获取到图片数据")
    else:
        print(f"\n❌ 生成失败: {result.get('message')}")

if __name__ == "__main__":
    main()
