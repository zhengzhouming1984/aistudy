"""
测试RAG服务的聊天记录功能
功能：验证rag.py是否正确实现了对话历史记忆功能

测试流程：
1. 初始化RAG服务
2. 进行多轮对话
3. 验证AI是否能记住之前的对话内容
4. 检查聊天历史文件是否被正确创建和更新
"""

from rag import RagService

def test_chat_history():
    """
    测试聊天历史功能
    """
    print("=" * 60)
    print("开始测试RAG服务的聊天历史功能...")
    print("=" * 60)
    
    # 创建RAG服务实例
    rag_service = RagService()
    
    # 测试会话ID
    session_id = "test_session"
    
    # 第一轮对话：基本问题
    print("\n【第一轮对话】")
    print("-" * 40)
    query1 = "我身高1.66米，尺码推荐"
    print(f"用户问题: {query1}")
    
    response1 = rag_service.run(query1, session_id=session_id)
    print(f"AI回答: {response1}")
    
    # 第二轮对话：跟进问题
    print("\n【第二轮对话】")
    print("-" * 40)
    query2 = "那如果我体重是60公斤呢？"
    print(f"用户问题: {query2}")
    print("（这是一个跟进问题，应该结合之前的身高信息）")
    
    response2 = rag_service.run(query2, session_id=session_id)
    print(f"AI回答: {response2}")
    
    # 第三轮对话：测试历史记忆
    print("\n【第三轮对话】")
    print("-" * 40)
    query3 = "我之前问的身高是多少？"
    print(f"用户问题: {query3}")
    print("（测试AI是否记住了之前的身高信息）")
    
    response3 = rag_service.run(query3, session_id=session_id)
    print(f"AI回答: {response3}")
    
    # 第四轮对话：测试多轮上下文
    print("\n【第四轮对话】")
    print("-" * 40)
    query4 = "根据我之前的信息，推荐什么尺码？"
    print(f"用户问题: {query4}")
    print("（测试AI是否能结合所有历史信息）")
    
    response4 = rag_service.run(query4, session_id=session_id)
    print(f"AI回答: {response4}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("请检查 chat_history/test_session.json 文件，确认聊天记录已保存")
    print("=" * 60)

if __name__ == "__main__":
    test_chat_history()
