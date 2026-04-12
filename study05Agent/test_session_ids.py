#!/usr/bin/env python3
"""
测试 get_all_session_ids() 函数
"""

from chat_store import get_all_session_ids, get_chat_history

print("测试 get_all_session_ids() 函数")
try:
    session_ids = get_all_session_ids()
    print(f"获取到的会话ID数量: {len(session_ids)}")
    print("会话ID列表:")
    for session_id in session_ids:
        print(f"  - {session_id}")
        # 测试获取每个会话的聊天记录
        history = get_chat_history(session_id)
        print(f"    聊天记录数量: {len(history)}")
except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
