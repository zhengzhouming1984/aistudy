# test_model.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# 获取配置
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
chat_model = os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B")

print(f"测试模型: {chat_model}")
print(f"API Base URL: {base_url}")

# 初始化模型
try:
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=chat_model,
        temperature=0.7
    )
    
    # 测试模型响应
    response = llm.invoke("你好，测试一下模型是否正常工作")
    print(f"模型响应: {response.content}")
    print("✅ 模型测试成功！")
    
except Exception as e:
    print(f"❌ 模型测试失败: {str(e)}")