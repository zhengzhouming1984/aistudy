"""
智能客服应用
功能：基于RAG技术的智能客服系统，支持会话管理和聊天历史记录

主要功能：
1. 会话管理：创建、切换和管理聊天会话
2. 聊天历史：自动保存和加载聊天记录
3. 智能回答：基于知识库的检索增强生成
4. 界面美观：现代化的聊天界面设计

使用方法：
1. 打开应用后会自动创建新会话
2. 输入问题获取智能回答
3. 记录会话ID，下次使用相同ID可继续对话
"""

import streamlit as st
from rag import RagService
import time
import random
import json
import os
import datetime

# 设置页面配置
# 首次运行时，使用默认标题，会话ID生成后会更新
st.set_page_config(
    page_title=f"{st.session_state.get('session_id', 'zhengzhouming')}的助手",  # 页面标题，显示在浏览器标签页
    page_icon="🤖",  # 页面图标，显示在浏览器标签页
    layout="wide"  # 页面布局，宽屏模式
)

# 初始化会话状态
# 使用Streamlit的会话状态来存储应用状态，确保刷新页面后状态保持
if "rag_service" not in st.session_state:
    # 创建RAG服务实例，用于处理用户查询和生成回答
    st.session_state.rag_service = RagService()

# 生成或获取会话ID
if "session_id" not in st.session_state:
    # 生成基于时间戳的会话ID，确保唯一性
    st.session_state.session_id = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
    # 更新页面标题，显示当前会话ID
    st.set_page_config(
        page_title=st.session_state.session_id,
        page_icon="🤖",
        layout="wide"
    )

# 使用CSS样式
# 为应用添加自定义样式，设置主内容区域的上边距
st.markdown("""
<style>
    .main-content {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏：会话管理
# 创建侧边栏，用于管理会话和显示应用信息
with st.sidebar:
    st.title("会话管理")
    st.markdown("---")
    
    # 允许用户输入会话ID
    st.markdown("### 继续之前的对话")
    user_session_id = st.text_input("输入会话ID", value=st.session_state.session_id)
    
    # 如果用户输入了不同的会话ID，更新会话状态并加载聊天记录
    if user_session_id != st.session_state.session_id:
        # 更新会话ID
        st.session_state.session_id = user_session_id
        # 重置消息列表，准备加载新会话的历史记录
        st.session_state.messages = []
        
        # 尝试从文件加载聊天历史
        # 构建聊天历史文件路径
        chat_history_path = os.path.join(os.path.dirname(__file__), "chat_history", f"{st.session_state.session_id}.json")
        st.info(f"尝试加载聊天历史文件: {chat_history_path}")
        
        # 检查文件是否存在
        if os.path.exists(chat_history_path):
            try:
                # 读取并解析聊天历史文件
                with open(chat_history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 转换为Streamlit消息格式
                    for msg in data:
                        # 提取时间戳（如果有的话）
                        msg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if msg['type'] == 'human':
                            # 添加用户消息到会话状态
                            st.session_state.messages.append({"role": "user", "content": msg['data']['content'], "time": msg_time})
                        elif msg['type'] == 'ai':
                            # 添加AI消息到会话状态
                            st.session_state.messages.append({"role": "assistant", "content": msg['data']['content'], "time": msg_time})
                    # 显示加载成功信息
                    st.success(f"已切换到会话: {user_session_id}，并加载了 {len(st.session_state.messages)} 条历史消息")
            except Exception as e:
                # 显示加载失败信息
                st.error(f"加载聊天历史失败: {str(e)}")
        else:
            # 显示切换到新会话的信息
            st.success(f"已切换到新会话: {user_session_id}")
        
        # 更新页面标题，显示新的会话ID
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
# 使用CSS在Streamlit的header中添加会话ID显示
css_style = """
<style>
    /* 在Streamlit header中添加会话ID */
    .stAppHeader {
        position: relative;
    }
    
    /* 创建会话ID显示元素 */
    .stAppHeader::before {
        content: "SESSION_ID_PLACEHOLDER";
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
    }
    
    /* 调整顶部布局，为header中的会话ID留出空间 */
    .main-content {
        margin-top: 20px;
        padding-bottom: 30px;
    }
    
    /* 为聊天输入框添加底部间距 */
    .stChatInput {
        margin-bottom: 20px;
    }
</style>
"""

# 替换会话ID占位符
css_style = css_style.replace("SESSION_ID_PLACEHOLDER", st.session_state.session_id)

# 应用CSS样式
st.markdown(css_style, unsafe_allow_html=True)

# 主标题
st.title("智能客服")
st.divider()

# 加载聊天历史
# 初始化消息列表，如果不存在则创建
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # 尝试从文件加载聊天历史
    # 构建聊天历史文件路径
    chat_history_path = os.path.join(os.path.dirname(__file__), "chat_history", f"{st.session_state.session_id}.json")
    st.info(f"尝试加载聊天历史文件: {chat_history_path}")
    
    # 检查文件是否存在
    if os.path.exists(chat_history_path):
        try:
            # 读取并解析聊天历史文件
            with open(chat_history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换为Streamlit消息格式
                for msg in data:
                    # 提取时间戳（如果有的话）
                    msg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if msg['type'] == 'human':
                        # 添加用户消息到会话状态
                        st.session_state.messages.append({"role": "user", "content": msg['data']['content'], "time": msg_time})
                    elif msg['type'] == 'ai':
                        # 添加AI消息到会话状态
                        st.session_state.messages.append({"role": "assistant", "content": msg['data']['content'], "time": msg_time})
                # 显示加载成功信息
                st.success(f"已加载 {len(st.session_state.messages)} 条历史消息")
        except Exception as e:
            # 显示加载失败信息
            st.error(f"加载聊天历史失败: {str(e)}")

# 定义用户名
USER_NAME = "用户"
AI_NAME = "智能客服"

# 显示历史消息
# 遍历会话状态中的所有消息并显示
for message in st.session_state.messages:
    # 使用Streamlit的chat_message组件显示消息
    with st.chat_message(message["role"]):
        # 确定用户名
        username = USER_NAME if message["role"] == "user" else AI_NAME
        # 显示时间戳和用户名
        timestamp = message.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.markdown(f"**{username}** - {timestamp}")
        # 另起一行显示内容
        st.markdown(message["content"])

# 使用chat_input创建聊天输入框
# 捕获用户输入的问题
prompt = st.chat_input("请输入您的问题")

# 处理用户输入
if prompt:
    # 获取当前时间，用于消息时间戳
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加用户消息到会话状态
    st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(f"**{USER_NAME}** - {current_time}")
        st.markdown(prompt)
    
    # 调用RAG服务获取回答
    # 使用spinner显示加载状态
    with st.spinner("正在思考..."):
        # 调用RAG服务处理用户查询，传入会话ID
        response = st.session_state.rag_service.run(prompt, session_id=st.session_state.session_id)
    
    # 获取回答时间
    response_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 添加AI回答到会话状态
    st.session_state.messages.append({"role": "assistant", "content": response, "time": response_time})
    
    # 显示AI回答
    with st.chat_message("assistant"):
        st.markdown(f"**{AI_NAME}** - {response_time}")
        st.markdown(response)
