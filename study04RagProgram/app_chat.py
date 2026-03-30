import streamlit as st
from rag import RagService
import time
import random
import json
import os
import datetime

# 设置页面配置
st.set_page_config(
    page_title=f"{st.session_state.get('session_id', '郑州明的助手')}",
    page_icon="🤖",
    layout="wide"
)

# 初始化会话状态
if "rag_service" not in st.session_state:
    st.session_state.rag_service = RagService()

# 生成或获取会话ID
if "session_id" not in st.session_state:
    # 生成基于时间戳的会话ID
    st.session_state.session_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
    # 更新页面标题
    st.set_page_config(
        page_title=st.session_state.session_id,
        page_icon="🤖",
        layout="wide"
    )

# 使用CSS样式
st.markdown("""
<style>
    .main-content {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏：会话管理
with st.sidebar:
    st.title("会话管理")
    st.markdown("---")
    
    # 允许用户输入会话ID
    st.markdown("### 继续之前的对话")
    user_session_id = st.text_input("输入会话ID", value=st.session_state.session_id)
    
    # 如果用户输入了不同的会话ID，更新会话状态并加载聊天记录
    if user_session_id != st.session_state.session_id:
        st.session_state.session_id = user_session_id
        # 重置消息列表
        st.session_state.messages = []
        
        # 尝试从文件加载聊天历史
        chat_history_path = os.path.join(os.path.dirname(__file__), "chat_history", f"{st.session_state.session_id}.json")
        st.info(f"尝试加载聊天历史文件: {chat_history_path}")
        if os.path.exists(chat_history_path):
            try:
                with open(chat_history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换为Streamlit消息格式
                    for msg in data:
                        # 提取时间戳（如果有的话）
                        msg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if msg['type'] == 'human':
                            st.session_state.messages.append({"role": "user", "content": msg['data']['content'], "time": msg_time})
                        elif msg['type'] == 'ai':
                            st.session_state.messages.append({"role": "assistant", "content": msg['data']['content'], "time": msg_time})
                    st.success(f"已切换到会话: {user_session_id}，并加载了 {len(st.session_state.messages)} 条历史消息")
            except Exception as e:
                st.error(f"加载聊天历史失败: {str(e)}")
        else:
            st.success(f"已切换到新会话: {user_session_id}")
        # 更新页面标题
        st.set_page_config(
            page_title=st.session_state.session_id,
            page_icon="🤖",
            layout="wide"
        )
    
    # 显示当前会话ID（放在输入框后面，确保显示最新的会话ID）
    st.markdown("\n### 当前会话ID")
    st.code(st.session_state.session_id)
    st.markdown("\n**重要提示：** 记录此会话ID，下次使用相同ID可以继续对话")
    
    st.markdown("---")
    st.markdown("### 关于")
    st.markdown("这是一个基于RAG的智能客服系统，")
    st.markdown("可以回答关于尺码推荐、洗涤养护等问题。")

# 在顶部添加会话ID显示，与Deploy按钮对齐
st.markdown(f"""
<style>
    /* 在Streamlit header中添加会话ID */
    .stAppHeader {{
        position: relative;
    }}
    
    /* 创建会话ID显示元素 */
    .stAppHeader::before {{
        content: "{st.session_state.session_id}";
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        color: white;
        font-size: 16px;
        font-weight: bold;
        z-index: 1000;
        padding: 8px 16px;
        background-color: rgba(14, 17, 23, 0.9);
        border-radius: 4px;
    }}
    
    /* 调整顶部布局，为header中的会话ID留出空间 */
    .main-content {{
        margin-top: 20px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("智能客服")
st.divider()

# 加载聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # 尝试从文件加载聊天历史
    chat_history_path = os.path.join(os.path.dirname(__file__), "chat_history", f"{st.session_state.session_id}.json")
    st.info(f"尝试加载聊天历史文件: {chat_history_path}")
    if os.path.exists(chat_history_path):
        try:
            with open(chat_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换为Streamlit消息格式
                for msg in data:
                    # 提取时间戳（如果有的话）
                    msg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if msg['type'] == 'human':
                        st.session_state.messages.append({"role": "user", "content": msg['data']['content'], "time": msg_time})
                    elif msg['type'] == 'ai':
                        st.session_state.messages.append({"role": "assistant", "content": msg['data']['content'], "time": msg_time})
                st.success(f"已加载 {len(st.session_state.messages)} 条历史消息")
        except Exception as e:
            st.error(f"加载聊天历史失败: {str(e)}")

# 定义用户名
USER_NAME = "用户"
AI_NAME = "智能客服"

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 确定用户名
        username = USER_NAME if message["role"] == "user" else AI_NAME
        # 显示时间戳和用户名
        timestamp = message.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.markdown(f"**{username}** - {timestamp}")
        # 另起一行显示内容
        st.markdown(message["content"])

# 使用chat_input创建聊天输入框
prompt = st.chat_input("请输入您的问题")

if prompt:
    # 获取当前时间
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加用户消息到会话状态
    st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(f"**{USER_NAME}** - {current_time}")
        st.markdown(prompt)
    
    # 调用RAG服务获取回答
    with st.spinner("正在思考..."):
        response = st.session_state.rag_service.run(prompt, session_id=st.session_state.session_id)
    
    # 获取回答时间
    response_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加AI回答到会话状态
    st.session_state.messages.append({"role": "assistant", "content": response, "time": response_time})
    
    # 显示AI回答
    with st.chat_message("assistant"):
        st.markdown(f"**{AI_NAME}** - {response_time}")
        st.markdown(response)