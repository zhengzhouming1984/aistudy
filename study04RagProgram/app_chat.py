import streamlit as st
from rag import RagService
import time
import random
import json
import os

# 初始化会话状态
if "rag_service" not in st.session_state:
    st.session_state.rag_service = RagService()

# 生成或获取会话ID
if "session_id" not in st.session_state:
    # 生成基于时间戳的会话ID
    st.session_state.session_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"

# 侧边栏：会话管理
with st.sidebar:
    st.title("会话管理")
    st.markdown("---")
    
    # 显示当前会话ID
    st.markdown(f"### 当前会话ID")
    st.code(st.session_state.session_id)
    st.markdown("\n**重要提示：** 记录此会话ID，下次使用相同ID可以继续对话")
    
    # 允许用户输入会话ID
    st.markdown("\n### 继续之前的对话")
    user_session_id = st.text_input("输入会话ID", value=st.session_state.session_id)
    
    # 如果用户输入了不同的会话ID，更新会话状态并加载聊天记录
    if user_session_id != st.session_state.session_id:
        st.session_state.session_id = user_session_id
        # 重置消息列表
        st.session_state.messages = []
        
        # 尝试从文件加载聊天历史
        chat_history_path = f"./chat_history/{st.session_state.session_id}.json"
        if os.path.exists(chat_history_path):
            try:
                with open(chat_history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换为Streamlit消息格式
                    for msg in data:
                        if msg['type'] == 'human':
                            st.session_state.messages.append({"role": "user", "content": msg['data']['content']})
                        elif msg['type'] == 'ai':
                            st.session_state.messages.append({"role": "assistant", "content": msg['data']['content']})
                    st.success(f"已切换到会话: {user_session_id}，并加载了 {len(st.session_state.messages)} 条历史消息")
            except Exception as e:
                st.error(f"加载聊天历史失败: {str(e)}")
        else:
            st.success(f"已切换到新会话: {user_session_id}")
    
    st.markdown("---")
    st.markdown("### 关于")
    st.markdown("这是一个基于RAG的智能客服系统，")
    st.markdown("可以回答关于尺码推荐、洗涤养护等问题。")

st.title("智能客服")
st.divider()

# 加载聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # 尝试从文件加载聊天历史
    chat_history_path = f"./chat_history/{st.session_state.session_id}.json"
    if os.path.exists(chat_history_path):
        try:
            with open(chat_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换为Streamlit消息格式
                for msg in data:
                    if msg['type'] == 'human':
                        st.session_state.messages.append({"role": "user", "content": msg['data']['content']})
                    elif msg['type'] == 'ai':
                        st.session_state.messages.append({"role": "assistant", "content": msg['data']['content']})
                st.success(f"已加载 {len(st.session_state.messages)} 条历史消息")
        except Exception as e:
            st.error(f"加载聊天历史失败: {str(e)}")

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 使用chat_input创建聊天输入框
prompt = st.chat_input("请输入您的问题")

if prompt:
    # 添加用户消息到会话状态
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    st.chat_message("user").write(prompt)
    
    # 调用RAG服务获取回答
    with st.spinner("正在思考..."):
        response = st.session_state.rag_service.run(prompt, session_id=st.session_state.session_id)
    
    # 添加AI回答到会话状态
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 显示AI回答
    st.chat_message("assistant").write(response)