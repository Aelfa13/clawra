#!/usr/bin/env python3
"""
野甜自拍 - 使用即梦4.0生成图片
"""
import json
import os
import sys
import time
import base64
import hashlib
import urllib.request
from volcengine.visual.VisualService import VisualService

# 配置
CONFIG_PATH = os.path.expanduser("~/.openclaw/config/jimeng/config.json")
REFERENCE_IMAGE = os.path.expanduser("~/.openclaw/workspace/clawra/skill/assets/clawra.jpg")

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
        return f"{user_context}, a close-up selfie taken by herself, direct eye contact with the camera, looking straight into the lens, eyes centered and clearly visible, not a mirror selfie, phone held at arm's length, face fully visible"
    else:
        return f"{user_context}, the person is taking a mirror selfie, full body shot"

def download_image(url, filename=None):
    """下载图片"""
    if filename is None:
        ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'
        hash_name = hashlib.md5(url.encode()).hexdigest()[:12]
        filename = f"selfie_{hash_name}{ext}"
    
    local_path = f"/tmp/{filename}"
    
    if os.path.exists(local_path):
        return local_path
    
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    
    with open(local_path, 'wb') as f:
        f.write(data)
    
    return local_path

def wait_for_result(service, task_id, req_key, max_wait=180, interval=2):
    """等待任务完成"""
    for i in range(max_wait // interval):
        time.sleep(interval)
        
        query_body = {
            "req_key": req_key,
            "task_id": task_id,
            "req_json": json.dumps({"return_url": True})
        }
        
        r2 = service.cv_sync2async_get_result(query_body)
        
        if r2.get("code") == 10000:
            status = r2["data"]["status"]
            
            if status == "done":
                image_urls = r2["data"].get("image_urls", [])
                local_files = []
                for i, url in enumerate(image_urls):
                    try:
                        local_path = download_image(url, f"selfie_{i}.jpg")
                        local_files.append(local_path)
                    except Exception as e:
                        print(f"下载失败: {e}")
                
                return local_files
    
    return []

def generate_selfie(user_context):
    """生成自拍图片"""
    service = create_service()
    mode = detect_mode(user_context)
    prompt = build_prompt(user_context, mode)
    
    print(f"模式: {mode}")
    print(f"提示词: {prompt}")
    
    if not os.path.exists(REFERENCE_IMAGE):
        raise Exception(f"参考图不存在: {REFERENCE_IMAGE}")
    
    # 上传参考图获取URL (简化处理 - 直接用本地路径)
    # 即梦需要URL，先上传到可访问的地方
    print("提交图生图任务...")
    
    # 使用 jimeng_t2i_v40 + image_urls 参数
    # 先上传参考图到即梦获取URL
    # 这里简化处理，假设即梦支持本地路径或已经上传的URL
    
    # 读取参考图
    with open(REFERENCE_IMAGE, 'rb') as f:
        img_data = f.read()
    img_base64 = base64.b64encode(img_data).decode()
    
    # 尝试用 base64 方式
    body = {
        "req_key": "jimeng_img2img_v20",  # 尝试旧版API
        "prompt": prompt,
        "image_base64": img_base64,
        "size": 4194304,
        "force_single": True
    }
    
    result = service.cv_sync2async_submit_task(body)
    
    if result.get("code") != 10000:
        # 尝试 t2i 模式
        print(f"img2img 失败，尝试文生图模式...")
        body = {
            "req_key": "jimeng_t2i_v40",
            "prompt": prompt,
            "size": 4194304,
            "force_single": True
        }
        result = service.cv_sync2async_submit_task(body)
    
    if result.get("code") != 10000:
        raise Exception(f"提交失败: {result}")
    
    task_id = result["data"]["task_id"]
    print(f"任务ID: {task_id}")
    print("等待生成...")
    
    req_key = result.get("data", {}).get("req_key", "jimeng_t2i_v40")
    local_files = wait_for_result(service, task_id, req_key)
    
    if not local_files:
        raise Exception("生成失败，未获取到图片")
    
    return local_files

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
