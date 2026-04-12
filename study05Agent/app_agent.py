"""
Agent应用
功能：基于OpenAI模型的智能agent应用，支持MCP功能

主要功能：
1. 智能对话：与agent进行自然语言对话
2. MCP功能：调用外部工具和服务
3. 上下文管理：维护对话历史
4. 知识库查询：通过RAG工具查询知识库

使用方法：
1. 打开应用后输入问题
2. agent会根据问题选择合适的工具
3. 查看agent的处理过程和结果
"""

import streamlit as st
from agent import AgentService
from chat_store import get_chat_history, get_all_session_ids, delete_session
import time
import random
import datetime

# 设置页面配置
st.set_page_config(
    page_title="智能Agent",
    page_icon="🤖",
    layout="wide"
)

# 生成或获取会话ID
if "session_id" not in st.session_state:
    st.session_state.session_id = f"agent_{int(time.time())}_{random.randint(1000, 9999)}"

# 初始化会话状态
if "agent_service" not in st.session_state:
    st.session_state.agent_service = AgentService(st.session_state.session_id)
# 如果session_id改变，重新创建AgentService实例
elif hasattr(st.session_state.agent_service, 'session_id') and st.session_state.agent_service.session_id != st.session_state.session_id:
    st.session_state.agent_service = AgentService(st.session_state.session_id)

# 使用CSS样式
st.markdown('''
<style>
    .main-content {
        margin-top: 20px;
        padding-bottom: 30px;
    }
    .stChatInput {
        margin-bottom: 20px;
    }
    .agent-thought {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-style: italic;
    }
</style>
''', unsafe_allow_html=True)

# 侧边栏：会话管理
with st.sidebar:
    st.title("Agent管理")
    st.markdown("---")
    
    # 显示当前会话ID
    st.markdown("### 当前会话ID")
    st.code(st.session_state.session_id)
    
    st.markdown("---")
    
    # 历史会话选择
    st.markdown("### 历史会话")
    try:
        session_ids = get_all_session_ids()
        if session_ids:
            selected_session = st.selectbox(
                "选择历史会话",
                session_ids,
                index=None,
                placeholder="选择一个会话ID查看历史记录"
            )
            
            if selected_session:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("查看历史会话"):
                        # 加载历史会话记录
                        history = get_chat_history(selected_session)
                        st.session_state.session_id = selected_session
                        st.session_state.agent_service = AgentService(selected_session)
                        st.session_state.messages = []
                        for msg in history:
                            st.session_state.messages.append({"role": msg["role"], "content": msg["content"], "time": msg["time"]})
                        st.experimental_rerun()
                with col2:
                    if st.button("删除会话", key="delete_session"):
                        # 删除会话记录
                        if delete_session(selected_session):
                            st.success(f"会话 {selected_session} 已删除")
                            # 刷新页面
                            st.experimental_rerun()
                        else:
                            st.error("删除会话失败")
        else:
            st.markdown("暂无历史会话")
    except Exception as e:
        st.markdown("加载历史会话失败")
    
    st.markdown("---")
    st.markdown("### 关于")
    st.markdown("这是一个基于OpenAI模型的智能agent，")
    st.markdown("支持MCP功能和知识库查询。")
    
    st.markdown("---")
    st.markdown("### 示例问题")
    st.markdown("- 你好，介绍一下你自己")
    st.markdown("- 查询知识库：如何选择合适的尺码")
    st.markdown("- 调用MCP：weather|北京")

# 主标题
st.title("智能Agent")
st.divider()

# 加载聊天历史
if "messages" not in st.session_state:
    # 尝试从SQLite数据库加载聊天历史
    try:
        history = get_chat_history(st.session_state.session_id)
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"], "time": msg["time"]})
        st.session_state.messages = messages
    except Exception as e:
        print(f"加载聊天历史失败: {str(e)}")
        st.session_state.messages = []

# 定义用户名
USER_NAME = "用户"
AGENT_NAME = "智能Agent"

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        username = USER_NAME if message["role"] == "user" else AGENT_NAME
        timestamp = message.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.markdown(f"**{username}** - {timestamp}")
        st.markdown(message["content"])
        
        # 显示agent思考过程（如果有）
        if message.get("thought"):
            st.markdown(f"<div class='agent-thought'>{message['thought']}</div>", unsafe_allow_html=True)

# 使用chat_input创建聊天输入框
prompt = st.chat_input("请输入您的问题")

# 处理用户输入
if prompt:
    # 获取当前时间
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加用户消息到会话状态
    st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(f"**{USER_NAME}** - {current_time}")
        st.markdown(prompt)
    
    # 调用Agent服务获取回答
    with st.spinner("正在思考..."):
        # 调用Agent服务处理用户查询
        response = st.session_state.agent_service.run(prompt)
    
    # 获取回答时间
    response_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加Agent回答到会话状态
    st.session_state.messages.append({"role": "assistant", "content": response, "time": response_time})
    
    # 显示Agent回答
    with st.chat_message("assistant"):
        st.markdown(f"**{AGENT_NAME}** - {response_time}")
        st.markdown(response)
