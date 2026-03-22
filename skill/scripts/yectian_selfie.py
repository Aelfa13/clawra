#!/usr/bin/env python3
"""
野甜自拍 - 使用即梦4.0生成图片
"""
import json
import os
import sys
import base64
from volcengine.visual.VisualService import VisualService

# 配置
CONFIG_PATH = os.path.expanduser("~/.openclaw/config/jimeng/config.json")
REFERENCE_IMAGE = os.path.expanduser("~/.openclaw/workspace/clawra/skill/assets/clawra.jpg")

# 固定的相似度提示词 - 严格保持人物一致性
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
    "regardless of: angle changes, camera distance, lighting changes, pose changes, clothing changes, background changes, "
    "face must remain completely consistent (90%+ similarity), "
    "high realistic photography style, detailed skin texture, realistic lighting, natural look, "
    "forbidden: female, forbidden: very short hair, forbidden: pixie cut, forbidden: long hair, forbidden: beard, forbidden: stubble, "
    "forbidden: changing facial features, forbidden: changing skin tone, forbidden: person deformation, "
    "forbidden: younger face, forbidden: dull expression"
)

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def create_service():
    config = load_config()
    service = VisualService()
    service.set_ak(config["access_key_id"])
    service.set_sk(config["secret_key"])
    return service

def detect_mode(user_context):
    """检测自拍模式"""
    direct_keywords = ['cafe', 'restaurant', 'beach', 'park', 'city', 'close-up', 'portrait', 'face', 'eyes', 'smile', '咖啡', '餐厅', '海边', '公园', '城市', '特写', '自拍', '微笑', '镜头', '写真']
    mirror_keywords = ['outfit', 'wearing', 'clothes', 'dress', 'suit', 'fashion', 'full-body', 'mirror', '穿', '衣服', '服装', '全身', '镜', '换装']
    
    ctx = user_context.lower()
    for kw in direct_keywords:
        if kw in ctx:
            return 'direct'
    for kw in mirror_keywords:
        if kw in ctx:
            return 'mirror'
    return 'mirror'

def build_prompt(user_context, mode):
    """构建提示词"""
    if mode == 'direct':
        return f"{user_context}, {IDENTITY_PROMPT}, close-up selfie, direct eye contact with the camera, looking straight into the lens, not a mirror selfie, phone held at arm's length, face fully visible"
    else:
        return f"{user_context}, {IDENTITY_PROMPT}, mirror selfie, full body shot"

def generate_selfie(user_context):
    """生成自拍图片"""
    service = create_service()
    mode = detect_mode(user_context)
    prompt = build_prompt(user_context, mode)
    
    print(f"模式: {mode}")
    print(f"提示词: {prompt}")
    
    if not os.path.exists(REFERENCE_IMAGE):
        raise Exception(f"参考图不存在: {REFERENCE_IMAGE}")
    
    # 读取参考图并转 base64
    with open(REFERENCE_IMAGE, 'rb') as f:
        img_data = f.read()
    img_base64 = base64.b64encode(img_data).decode()
    
    print("提交图生图任务...")
    
    body = {
        "req_key": "jimeng_t2i_v40",
        "prompt": prompt,
        "image_base64": img_base64,
        "size": 4194304,
        "force_single": True
    }
    
    result = service.cv_process(body)
    
    if result.get("code") != 10000:
        raise Exception(f"提交失败: {result.get('message')}")
    
    # 获取图片数据
    data = result.get("data", {})
    b64_data = data.get("binary_data_base64", [])
    
    if not b64_data:
        raise Exception("生成失败，未获取到图片数据")
    
    # 保存图片
    img_bytes = base64.b64decode(b64_data[0])
    filepath = f"/tmp/yectian_selfie_{os.getpid()}.jpg"
    with open(filepath, 'wb') as f:
        f.write(img_bytes)
    
    return [filepath]

def main():
    if len(sys.argv) < 2:
        print("Usage: python yectian_selfie.py <user_context>")
        sys.exit(1)
    
    user_context = sys.argv[1]
    
    try:
        files = generate_selfie(user_context)
        
        print(f"\n生成了 {len(files)} 张图片:")
        for f in files:
            print(f"  {f}")
        
        print("\n[OUTPUT_JSON]")
        print(json.dumps({
            "success": True,
            "files": files,
            "count": len(files)
        }))
        
    except Exception as e:
        print(f"错误: {e}")
        print("\n[OUTPUT_JSON]")
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
