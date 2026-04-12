import sqlite3 
import uuid 
import os
from dotenv import load_dotenv
from datetime import datetime 
import chromadb 
from chromadb.utils import embedding_functions

# 加载环境变量
load_dotenv() 

# ====================== 1. 初始化配置 ====================== 
# 1.1 SQLite 数据库文件（持久化存储） 
SQLITE_DB_PATH = "agent_chat.db" 

# 1.2 Chroma 向量数据库（持久化存储到本地文件夹） 
CHROMA_PERSIST_PATH = "./chroma_db" 
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH) 

# 1.3 向量嵌入模型（本地轻量模型，无需GPU） 
try:
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction( 
        model_name=os.getenv("VECTOR_EMBEDDING_MODEL", "all-MiniLM-L6-v2") 
    ) 
except Exception as e:
    print(f"加载嵌入模型失败: {str(e)}")
    # 使用默认嵌入函数作为备用
    embedding_func = None

# 1.4 获取/创建向量集合（一个会话一个collection，或统一用一个） 
try:
    collection = chroma_client.get_or_create_collection( 
        name="chat_vectors", 
        embedding_function=embedding_func, 
        metadata={"description": "Agent 聊天记录向量库"} 
    )
except Exception as e:
    print(f"创建向量集合失败: {str(e)}")
    collection = None 

# ====================== 2. SQLite 初始化（建表） ====================== 
def init_sqlite(): 
    """初始化聊天记录表"""
    conn = sqlite3.connect(SQLITE_DB_PATH) 
    cursor = conn.cursor() 

    # 聊天记录表：存储完整对话 
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS chat_messages ( 
            id TEXT PRIMARY KEY, 
            session_id TEXT NOT NULL, 
            role TEXT NOT NULL, 
            content TEXT NOT NULL, 
            create_time TIMESTAMP NOT NULL, 
            UNIQUE(id) 
        ) 
    ''') 

    conn.commit() 
    conn.close() 

# ====================== 3. 工具函数 ====================== 
def split_text(text: str, max_chunk_size: int = 300) -> list: 
    """简单文本分块：按长度分割（可替换为更智能的分块）"""
    chunks = [] 
    while len(text) > max_chunk_size: 
        chunks.append(text[:max_chunk_size]) 
        text = text[max_chunk_size:] 
    if text: 
        chunks.append(text) 
    return chunks 

# ====================== 4. 核心存储函数 ====================== 
def save_chat_message(session_id: str, role: str, content: str): 
    """
    统一保存聊天记录：同时存入 SQLite + 向量数据库 
    :param session_id: 会话ID 
    :param role: user/assistant 
    :param content: 消息内容 
    """
    # 生成唯一ID 
    msg_id = str(uuid.uuid4()) 
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

    # ---------------- 1. 保存到 SQLite ---------------- 
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH) 
        cursor = conn.cursor() 
        cursor.execute( 
            "INSERT INTO chat_messages (id, session_id, role, content, create_time) VALUES (?, ?, ?, ?, ?)", 
            (msg_id, session_id, role, content, now) 
        ) 
        conn.commit() 
        conn.close() 
    except Exception as e:
        print(f"保存到SQLite失败: {str(e)}")
        return msg_id

    # ---------------- 2. 文本分块 + 保存到向量库 ---------------- 
    if collection:
        try:
            text_chunks = split_text(content)  # 分块 

            # 为每个分块生成唯一向量ID 
            chunk_ids = [f"{msg_id}_chunk_{i}" for i in range(len(text_chunks))] 

            # 元数据：方便后续溯源 
            metadatas = [ 
                { 
                    "session_id": session_id, 
                    "role": role, 
                    "msg_id": msg_id, 
                    "chunk_index": i 
                } for i in range(len(text_chunks)) 
            ] 

            # 存入向量库 
            collection.add( 
                ids=chunk_ids, 
                documents=text_chunks, 
                metadatas=metadatas 
            ) 
            print(f"✅ 消息已保存 | SQLite ID: {msg_id} | 向量分块数: {len(text_chunks)}") 
        except Exception as e:
            print(f"保存到向量库失败: {str(e)}")
    else:
        print(f"✅ 消息已保存到SQLite | ID: {msg_id}") 
    
    return msg_id 

# ====================== 5. 聊天记录查询 ======================
def get_chat_history(session_id: str, limit: int = 20): 
    """从SQLite查询指定会话的历史聊天记录"""
    conn = sqlite3.connect(SQLITE_DB_PATH) 
    cursor = conn.cursor() 
    cursor.execute(''' 
        SELECT role, content, create_time FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY create_time ASC LIMIT ? 
    ''', (session_id, limit)) 
    records = cursor.fetchall() 
    conn.close() 

    # 格式化输出 
    history = [{"role": r[0], "content": r[1], "time": r[2]} for r in records] 
    return history

def get_all_session_ids():
    """获取所有会话ID"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT session_id FROM chat_messages
        GROUP BY session_id
        ORDER BY MAX(create_time) DESC
    ''')
    session_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return session_ids

def delete_session(session_id):
    """删除指定会话的所有聊天记录"""
    try:
        # 删除 SQLite 中的记录
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        # 删除会话的所有聊天记录
        cursor.execute('''
            DELETE FROM chat_messages WHERE session_id = ?
        ''', (session_id,))
        conn.commit()
        conn.close()
        
        # 删除 Chroma 中的记录
        if collection:
            try:
                # 查找并删除该会话的所有向量记录
                results = collection.get(where={"session_id": session_id})
                if results and "ids" in results and results["ids"]:
                    collection.delete(ids=results["ids"])
                    print(f"✅ 会话 {session_id} 的向量记录已删除")
            except Exception as e:
                print(f"删除向量记录失败: {str(e)}")
        
        print(f"✅ 会话 {session_id} 已删除")
        return True
    except Exception as e:
        print(f"删除会话失败: {str(e)}")
        return False 

# ====================== 6. 向量检索（RAG核心） ====================== 
def search_chat_vectors(query: str, session_id: str = None, top_k: int = 3): 
    """
    从向量库检索相似聊天记录 
    :param query: 检索问题 
    :param session_id: 可选：只检索某个会话 
    :param top_k: 返回最相似的topk条 
    """
    if not collection:
        print("向量库未初始化，无法进行检索")
        return []
    
    try:
        # 过滤条件（可选） 
        where_filter = {"session_id": session_id} if session_id else None 

        # 向量检索 
        results = collection.query( 
            query_texts=[query], 
            n_results=top_k, 
            where=where_filter 
        ) 

        # 格式化结果 
        matches = [] 
        for doc, meta, dist in zip( 
            results["documents"][0], 
            results["metadatas"][0], 
            results["distances"][0] 
        ):
            matches.append({ 
                "content": doc, 
                "metadata": meta, 
                "similarity": 1 - dist  # 余弦相似度 
            }) 
        return matches
    except Exception as e:
        print(f"向量检索失败: {str(e)}")
        return [] 

# 初始化数据库
init_sqlite()
