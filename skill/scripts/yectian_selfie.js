#!/usr/bin/env node
/**
 * 野甜自拍 - 使用即梦4.0生成图片 (Node.js版本)
 */
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 配置
const CONFIG_PATH = '/home/node/.openclaw/config/jimeng/config.json';
const REFERENCE_IMAGE = '/home/node/.openclaw/workspace/clawra/skill/assets/clawra.jpg';

function loadConfig() {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
}

function detectMode(userContext) {
    const directKeywords = ['cafe', 'restaurant', 'beach', 'park', 'city', 'close-up', 'portrait', 'face', 'eyes', 'smile', '咖啡', '餐厅', '海边', '公园', '城市', '特写', '自拍', '微笑'];
    const mirrorKeywords = ['outfit', 'wearing', 'clothes', 'dress', 'suit', 'fashion', 'full-body', 'mirror', '穿', '衣服', '服装', '全身'];
    
    const ctx = userContext.toLowerCase();
    for (const kw of directKeywords) if (ctx.includes(kw)) return 'direct';
    for (const kw of mirrorKeywords) if (ctx.includes(kw)) return 'mirror';
    return 'mirror';
}

function buildPrompt(userContext, mode) {
    if (mode === 'direct') {
        return `${userContext}, a close-up selfie taken by herself, direct eye contact with the camera, looking straight into the lens, eyes centered and clearly visible, not a mirror selfie, phone held at arm's length, face fully visible`;
    }
    return `${userContext}, the person is taking a mirror selfie`;
}

function downloadFile(url, filename) {
    return new Promise((resolve, reject) => {
        const filepath = `/tmp/${filename}`;
        if (fs.existsSync(filepath)) {
            console.log(`使用缓存: ${filepath}`);
            resolve(filepath);
            return;
        }
        
        const file = fs.createWriteStream(filepath);
        https.get(url, (res) => {
            if (res.statusCode === 301 || res.statusCode === 302) {
                downloadFile(res.headers.location, filename).then(resolve).catch(reject);
                return;
            }
            res.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log(`下载完成: ${filepath}`);
                resolve(filepath);
            });
        }).on('error', (err) => {
            fs.unlink(filepath, () => {});
            reject(err);
        });
    });
}

async function generateSelfie(userContext) {
    const config = loadConfig();
    const mode = detectMode(userContext);
    const prompt = buildPrompt(userContext, mode);
    
    console.log(`模式: ${mode}`);
    console.log(`提示词: ${prompt}`);
    
    // 读取参考图
    if (!fs.existsSync(REFERENCE_IMAGE)) {
        throw new Error(`参考图不存在: ${REFERENCE_IMAGE}`);
    }
    
    // 准备图片URL列表（即梦支持本地路径或URL）
    // 这里需要先上传参考图获取URL，或者直接使用本地路径
    
    // 由于火山引擎API需要先上传图片，我们先尝试直接调用API
    // 使用图生图模式
    
    // 构造请求
    const body = JSON.stringify({
        req_key: 'jimeng_img2img_v21',
        prompt: prompt,
        size: 4194304, // 2048x2048
        force_single: true,
        image_urls: [REFERENCE_IMAGE] // 即梦支持本地路径
    });
    
    console.log('提交生成任务...');
    
    // 这里简化处理，实际需要火山引擎签名验证
    console.log('注意: 需要完整的火山引擎签名才能调用API');
    console.log('备选方案: 使用Python脚本通过agent执行');
    
    return [];
}

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.log('Usage: node yectian_selfie.js <user_context> [--single]');
        process.exit(1);
    }
    
    const userContext = args[0];
    
    try {
        const files = await generateSelfie(userContext);
        if (files.length > 0) {
            console.log(`\n生成了 ${files.length} 张图片:`);
            files.forEach(f => console.log(`  ${f}`));
            console.log('\n[OUTPUT_JSON]');
            console.log(JSON.stringify({ success: true, files, count: files.length }));
        } else {
            console.log('\n[OUTPUT_JSON]');
            console.log(JSON.stringify({ success: false, error: 'No files generated' }));
        }
    } catch (err) {
        console.error('错误:', err.message);
        console.log('\n[OUTPUT_JSON]');
        console.log(JSON.stringify({ success: false, error: err.message }));
        process.exit(1);
    }
}

main();
