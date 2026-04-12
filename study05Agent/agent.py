"""
Agent模块
功能：实现基于OpenAI模型的智能agent，支持MCP功能

核心功能：
1. 智能对话：使用OpenAI模型进行对话
2. MCP功能：支持调用外部工具和服务
3. 上下文管理：维护对话历史
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from chat_store import save_chat_message, get_chat_history, search_chat_vectors

# 加载环境变量
load_dotenv()

class AgentService:
    """
    Agent服务类
    提供智能对话和MCP功能
    """
    
    def __init__(self, session_id):
        """
        初始化Agent服务
        
        Args:
            session_id (str): 会话ID
        """
        # 配置OpenAI模型
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("CHAT_MODEL", "Qwen/Qwen3-8B"),
            temperature=0.7
        )
        
        # 会话ID
        self.session_id = session_id
        # 初始化对话历史
        self.chat_history = self._load_chat_history()
    
    def _load_chat_history(self):
        """
        从SQLite加载聊天历史
        
        Returns:
            list: 聊天历史消息列表
        """
        try:
            # 从SQLite获取聊天历史
            history = get_chat_history(self.session_id)
            chat_history = []
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    chat_history.append(AIMessage(content=msg["content"]))
            return chat_history
        except Exception as e:
            print(f"加载聊天历史失败: {str(e)}")
            return []
    
    def _save_chat_history(self):
        """
        保存聊天历史到SQLite和向量数据库
        """
        try:
            # 只保存最后两条消息（用户消息和助手回复）
            if len(self.chat_history) >= 2:
                # 用户消息
                user_msg = self.chat_history[-2]
                if isinstance(user_msg, HumanMessage):
                    save_chat_message(self.session_id, "user", user_msg.content)
                # 助手消息
                ai_msg = self.chat_history[-1]
                if isinstance(ai_msg, AIMessage):
                    save_chat_message(self.session_id, "assistant", ai_msg.content)
        except Exception as e:
            print(f"保存聊天历史失败: {str(e)}")
    
    def rag_query_tool(self, query):
        """
        调用RAG服务进行查询
        
        Args:
            query (str): 查询内容
            
        Returns:
            str: 查询结果
        """
        # 这里可以调用study04RagProgram的RAG服务
        # 暂时返回模拟结果
        return f"RAG查询结果: {query}"
    
    def mcp_tool(self, action, params):
        """
        调用MCP功能
        
        Args:
            action (str): MCP动作
            params (dict): 动作参数
            
        Returns:
            str: MCP执行结果
        """
        # 处理天气查询
        if action == "查询天气" or action == "weather":
            city = params.strip()
            try:
                import requests
                api_key = os.getenv("WEATHER_API_KEY", "demo_key")
                
                # 使用 OpenWeatherMap API
                url = f"https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": city,
                    "appid": api_key,
                    "units": "metric",  # 使用摄氏度
                    "lang": "zh_cn"  # 中文结果
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                
                if response.status_code == 200:
                    weather = data["weather"][0]["description"]
                    temp = data["main"]["temp"]
                    humidity = data["main"]["humidity"]
                    wind_speed = data["wind"]["speed"]
                    
                    return f"{city}的天气：{weather}，温度：{temp}°C，湿度：{humidity}%，风速：{wind_speed}m/s"
                else:
                    return f"查询天气失败：{data.get('message', '城市未找到')}"
            except Exception as e:
                return f"天气查询错误：{str(e)}"
        
        # 其他MCP功能
        elif action == "时间" or action == "time":
            import datetime
            return f"当前时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 默认返回模拟结果
        return f"MCP执行结果: {action} with params {params}"
    
    def run(self, query):
        """
        运行agent处理查询
        
        Args:
            query (str): 用户查询
            
        Returns:
            str: 处理结果
        """
        try:
            # 构建提示
            messages = []
            
            # 添加系统提示
            system_prompt = """你是一个智能助手，能够帮助用户回答问题。你可以使用以下工具：

1. RAG查询工具：用于查询知识库，获取相关信息
   使用格式：RAG查询：<查询内容>

2. MCP工具：用于调用MCP功能，包括天气查询、时间查询等
   使用格式：MCP调用：<动作>|<参数>
   示例：
   - 天气查询：MCP调用：查询天气|福州
   - 时间查询：MCP调用：时间|

请根据用户的问题，决定是否使用工具，如果使用工具，请按照指定格式输出。
对于天气查询，请使用MCP工具，不要使用RAG工具。"""
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            for msg in self.chat_history:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
            
            # 添加当前查询
            messages.append({"role": "user", "content": query})
            
            # 调用模型
            response = self.llm.invoke(messages)
            
            # 处理模型响应
            response_content = response.content
            
            # 检查是否需要使用工具
            if "RAG查询：" in response_content:
                # 提取查询内容
                rag_query = response_content.split("RAG查询：")[1].strip()
                # 调用RAG工具
                rag_result = self.rag_query_tool(rag_query)
                # 将工具结果添加到对话
                self.chat_history.append(HumanMessage(content=query))
                self.chat_history.append(AIMessage(content=f"使用RAG查询工具：{rag_query}\n结果：{rag_result}"))
                # 保存聊天历史到Redis
                self._save_chat_history()
                return f"使用RAG查询工具：{rag_query}\n结果：{rag_result}"
            
            elif "MCP调用：" in response_content:
                # 提取动作和参数
                mcp_part = response_content.split("MCP调用：")[1].strip()
                if "|" in mcp_part:
                    action, params = mcp_part.split("|", 1)
                    # 调用MCP工具
                    mcp_result = self.mcp_tool(action.strip(), params.strip())
                    # 将工具结果添加到对话
                    self.chat_history.append(HumanMessage(content=query))
                    self.chat_history.append(AIMessage(content=f"使用MCP工具：{action.strip()}\n参数：{params.strip()}\n结果：{mcp_result}"))
                    # 保存聊天历史到Redis
                    self._save_chat_history()
                    return f"使用MCP工具：{action.strip()}\n参数：{params.strip()}\n结果：{mcp_result}"
            
            # 如果没有使用工具，直接返回回答
            self.chat_history.append(HumanMessage(content=query))
            self.chat_history.append(AIMessage(content=response_content))
            # 保存聊天历史到Redis
            self._save_chat_history()
            return response_content
            
        except Exception as e:
            return f"处理错误: {str(e)}"
