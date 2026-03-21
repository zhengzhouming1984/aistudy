#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 OpenAI 客户端调用 SiliconFlow API 的示例代码

功能：
- 初始化 OpenAI 客户端，连接到 SiliconFlow API
- 发送聊天完成请求，使用 Qwen3-8B 模型
- 流式处理响应，实时输出模型生成的内容
"""

from openai import OpenAI

# 初始化 OpenAI 客户端，配置 API 密钥和基础 URL
# 使用 SiliconFlow API 作为后端
client = OpenAI(
    api_key="sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw",  # API 密钥
    base_url="https://api.siliconflow.cn/v1"  # SiliconFlow API 基础 URL
)

# 发送聊天完成请求
response = client.chat.completions.create(
    # model='Pro/deepseek-ai/DeepSeek-R1',  # 备选模型
    model="Qwen/Qwen3-8B",  # 使用 Qwen3-8B 模型
    # model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",  # 使用 Qwen3-8B 模型
    messages=[
        {'role': 'user','content': "你的大模型是什么版本？"},  # 用户问题
        {'role': 'user','content': "你是谁"}  # 用户问题
    ],
    stream=True  # 启用流式响应，实时获取生成内容
)

# 处理流式响应
for chunk in response:
    # 跳过没有 choices 的响应块
    if not chunk.choices:
        continue
    
    # 输出模型的推理过程（如果有）
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
    
    # 输出模型生成的主要内容
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)