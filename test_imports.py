# 测试导入study01软件包
print("Testing study01 import...")
try:
    import sys
    sys.path.append('/Users/zhengzhouming/PycharmProjects/aistudy')
    from study01.InMemoryChatMessageHistory import get_session_history, conversation_chain
    from langchain_core.chat_history import InMemoryChatMessageHistory
    print("✓ study01 import successful")
except Exception as e:
    print(f"✗ study01 import failed: {e}")

# 测试导入study02软件包
print("\nTesting study02 import...")
try:
    import sys
    sys.path.append('/Users/zhengzhouming/PycharmProjects/aistudy')
    from study02.FileChatMessageHistory import FileChatMessageHistory, get_session_history, conversation_chain
    print("✓ study02 import successful")
except Exception as e:
    print(f"✗ study02 import failed: {e}")

print("\nImport test completed!")