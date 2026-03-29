"""
知识库服务模块
功能：提供知识库的管理、文件上传、查询和清空等功能

核心功能：
1. MD5去重：通过MD5值避免重复上传相同内容
2. 文本切分：支持语义切片和递归字符切片两种方式
3. 向量存储：使用Chroma数据库存储文本向量
4. 智能查询：根据关键词匹配优先返回相关文档
"""

import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from datetime import datetime
from langchain_openai import OpenAIEmbeddings

# ==================== MD5缓存管理 ====================

# 内存中的MD5缓存集合，用于提高查询效率
# 使用集合(Set)实现O(1)时间复杂度的查找
_md5_cache = set()

# 标记MD5缓存是否已从文件加载
_md5_cache_loaded = False


def _load_md5_cache():
    """
    从文件加载MD5缓存到内存
    
    首次调用时从md5.txt文件读取所有MD5值到内存缓存，
    后续查询直接从内存中查找，提高性能。
    """
    global _md5_cache, _md5_cache_loaded
    # 如果缓存未加载且文件存在，则加载
    if not _md5_cache_loaded and os.path.exists(config.md5_path):
        with open(config.md5_path, 'r', encoding='utf-8') as f:
            # 读取所有非空行并去除空白字符
            _md5_cache = set(line.strip() for line in f if line.strip())
        _md5_cache_loaded = True
        print(f"已加载 {len(_md5_cache)} 个MD5记录到缓存")


def check_md5(md5_str: str) -> bool:
    """
    检查MD5值是否已经处理过
    
    用于去重，避免重复上传相同内容。
    首次调用时会自动加载MD5缓存。
    
    Args:
        md5_str (str): 要检查的MD5字符串
        
    Returns:
        bool: True表示已经处理过（重复），False表示未处理过（新内容）
    """
    # 如果MD5文件不存在，创建空文件
    if not os.path.exists(config.md5_path):
        with open(config.md5_path, 'w', encoding='utf-8') as f:
            pass
        return False

    # 加载MD5缓存（首次调用）
    _load_md5_cache()
    
    # 在缓存中查找，时间复杂度O(1)
    return md5_str in _md5_cache


def save_md5(md5_str: str):
    """
    保存MD5值到文件和缓存
    
    将新内容的MD5值追加到文件，并更新内存缓存。
    会先检查是否已存在，避免重复记录。
    
    Args:
        md5_str (str): 要保存的MD5字符串
    """
    print(f"MD5文件路径: {config.md5_path}")
    
    # 确保文件存在
    if not os.path.exists(config.md5_path):
        with open(config.md5_path, 'w', encoding='utf-8') as f:
            pass
        print(f"创建了MD5文件: {config.md5_path}")
    
    # 先检查MD5是否已经存在，避免重复记录
    if not check_md5(md5_str):
        # 使用追加模式写入文件
        with open(config.md5_path, 'a', encoding='utf-8') as f:
            f.write(md5_str + "\n")
            f.flush()  # 确保内容立即写入文件
        print(f"MD5 {md5_str} 已保存")
        
        # 更新内存缓存
        global _md5_cache
        _md5_cache.add(md5_str)
    else:
        print(f"MD5 {md5_str} 已存在，跳过保存")


def get_string_md5(input_str: str, encoding: str = 'utf-8') -> str:
    """
    计算字符串的MD5哈希值
    
    Args:
        input_str (str): 输入字符串
        encoding (str): 编码格式，默认为utf-8
        
    Returns:
        str: 32位十六进制MD5字符串
    """
    # 将字符串编码为字节
    str_bytes = input_str.encode(encoding=encoding)
    # 计算MD5哈希并返回十六进制字符串
    return hashlib.md5(str_bytes).hexdigest()


# ==================== 嵌入模型初始化 ====================

# 初始化Qwen嵌入模型，用于文本向量化和语义切片
qwen_embeddings = OpenAIEmbeddings(
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
    model=config.embedding_model
)


# ==================== 知识库服务类 ====================

class KnowledgeBaseService(object):
    """
    知识库服务类
    
    提供知识库的完整管理功能，包括：
    - 文件上传：支持字符串上传和批量文件夹上传
    - 文本切分：支持语义切片和递归字符切片
    - 向量存储：使用Chroma数据库存储和检索
    - 智能查询：基于关键词的优先级排序
    - 去重管理：基于MD5值避免重复上传
    
    Attributes:
        chroma (Chroma): Chroma向量数据库实例
        spliter: 文本分割器实例（语义或递归字符）
    """
    
    def __init__(self):
        """
        初始化知识库服务
        
        初始化流程：
        1. 确保Chroma存储目录存在
        2. 初始化Chroma向量数据库
        3. 根据配置选择文本分割器
        """
        # 确保Chroma存储目录存在
        os.makedirs(config.chroma_path, exist_ok=True)
        
        # 初始化Chroma向量数据库
        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=qwen_embeddings,
            persist_directory=config.chroma_path
        )
        
        # 根据配置选择文本分割器
        if config.semantic_chunking:
            # 使用语义切片：基于语义相似度进行切分
            self.spliter = SemanticChunker(qwen_embeddings)
            print("-" * 50)
            print("使用语义切片器")
        else:
            # 使用递归字符切片：基于字符和分隔符进行切分
            self.spliter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                length_function=config.length_function,
                separators=config.separators,
                keep_separator=True
            )
            print("使用递归字符切片器")

    def upload_by_str(self, data: str, filename: str) -> str:
        """
        将字符串内容上传到知识库
        
        上传流程：
        1. 计算内容MD5值
        2. 检查是否已存在（去重）
        3. 文本切分
        4. 存入向量数据库
        5. 记录MD5值
        
        Args:
            data (str): 要上传的文本内容
            filename (str): 文件名，用于元数据记录
            
        Returns:
            str: 上传结果状态（成功/跳过/失败）
        """
        # 1. 计算MD5值
        md5_hex = get_string_md5(data)
        
        # 2. 检查是否已存在
        if check_md5(md5_hex):
            return "[跳过] 内容已经存在知识库中"
        
        try:
            # 3. 文本切分
            knowledge_chunks = self.spliter.split_text(data)
            if not knowledge_chunks:
                return "[错误] 文本切分后为空"
            
            # 打印切片信息
            print(f"\n文本切分完成，共切分成 {len(knowledge_chunks)} 个块")
            for i, chunk in enumerate(knowledge_chunks):
                print(f"\n--- 切片 {i+1} ---")
                print(f"长度：{len(chunk)} 字符")
                print(f"内容预览：{chunk[:200]}..." if len(chunk) > 200 else f"内容：{chunk}")
            
            # 4. 构建元数据并存入向量数据库
            metadata = {
                "source": filename,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "zhengzhouming"
            }
            
            self.chroma.add_texts(
                knowledge_chunks,
                metadatas=[{**metadata, "chunk_idx": i} for i in range(len(knowledge_chunks))]
            )
            
            # 5. 成功后记录MD5（避免失败却标记成功）
            save_md5(md5_hex)
            return "上传成功"
            
        except Exception as e:
            # 异常不写MD5，保证一致性
            return f"[失败]上传异常: {str(e)}"
    
    def clear_knowledge_base(self) -> str:
        """
        清空知识库
        
        清空内容包括：
        1. 向量数据库中的所有文档
        2. MD5记录文件
        3. 内存中的MD5缓存
        
        Returns:
            str: 清空操作的状态信息
        """
        try:
            # 清空向量数据库
            documents = self.chroma.get()
            if documents['ids']:
                self.chroma.delete(ids=documents['ids'])
                print(f"已删除 {len(documents['ids'])} 个文档")
            
            # 清空MD5记录文件
            print(f"MD5文件路径: {config.md5_path}")
            with open(config.md5_path, 'w', encoding='utf-8') as f:
                f.write('')
            print("MD5文件已清空")
            
            # 清空内存缓存
            global _md5_cache
            _md5_cache.clear()
            
            return "知识库和MD5记录已清空"
        except Exception as e:
            print(f"清空知识库失败: {str(e)}")
            return f"清空知识库失败: {str(e)}"
    
    def query_knowledge_base(self, query: str, k: int = 5) -> list:
        """
        查询知识库
        
        查询逻辑：
        1. 获取所有文档
        2. 根据查询关键词判断相关性
        3. 优先返回相关文档（前2个）
        
        关键词匹配：
        - 尺码/身高/体重 → 优先返回尺码推荐文档
        - 洗涤/养护/清洗 → 优先返回洗涤养护文档
        - 颜色/搭配 → 优先返回颜色选择文档
        
        Args:
            query (str): 查询字符串
            k (int): 返回结果数量，默认为5（实际返回前2个）
            
        Returns:
            list: 相关文档列表
        """
        try:
            # 获取所有文档
            all_docs = self.chroma.get()
            all_documents = []
            
            # 构建文档对象列表
            if all_docs and 'ids' in all_docs and 'documents' in all_docs and 'metadatas' in all_docs:
                for i, doc_id in enumerate(all_docs['ids']):
                    doc = type('Document', (), {
                        'page_content': all_docs['documents'][i],
                        'metadata': all_docs['metadatas'][i],
                        'id': doc_id
                    })()
                    all_documents.append(doc)
            
            # 检查查询关键词
            has_size_keywords = any(kw in query for kw in ["尺码", "身高", "体重"])
            has_wash_keywords = any(kw in query for kw in ["洗涤", "养护", "清洗", "羊绒衫"])
            has_color_keywords = any(kw in query for kw in ["颜色", "搭配"])
            
            # 根据关键词优先级排序
            relevant_docs = []
            other_docs = []
            
            for doc in all_documents:
                source = doc.metadata.get("source", "")
                content = doc.page_content
                
                # 根据关键词匹配判断相关性
                if has_size_keywords and ("尺码推荐" in source or "尺码" in content or "身高" in content or "体重" in content):
                    relevant_docs.append(doc)
                elif has_wash_keywords and ("洗涤养护" in source):
                    relevant_docs.append(doc)
                elif has_color_keywords and ("颜色选者" in source or "颜色" in content or "搭配" in content):
                    relevant_docs.append(doc)
                else:
                    other_docs.append(doc)
            
            # 合并结果，优先显示相关文档
            final_docs = relevant_docs + other_docs
            
            # 返回前2个结果
            return final_docs[:2]
        except Exception as e:
            print(f"查询知识库失败: {str(e)}")
            return []
    
    def upload_data_folder(self, data_folder: str = None) -> dict:
        """
        批量上传data文件夹下的所有txt文件
        
        Args:
            data_folder (str): data文件夹路径，默认为当前目录下的data文件夹
            
        Returns:
            dict: 上传结果统计，包含：
                - success: 成功上传的文件列表
                - skipped: 跳过的文件列表（重复内容）
                - failed: 上传失败的文件列表
        """
        # 使用默认路径
        if data_folder is None:
            data_folder = os.path.join(os.path.dirname(__file__), "data")
        
        # 初始化结果字典
        results = {
            "success": [],
            "skipped": [],
            "failed": []
        }
        
        # 检查文件夹是否存在
        if not os.path.exists(data_folder):
            print(f"数据文件夹不存在: {data_folder}")
            return results
        
        # 获取所有txt文件
        txt_files = [f for f in os.listdir(data_folder) if f.endswith('.txt')]
        
        if not txt_files:
            print(f"数据文件夹中没有txt文件: {data_folder}")
            return results
        
        print(f"\n开始批量上传，共找到 {len(txt_files)} 个txt文件")
        print("=" * 60)
        
        # 遍历上传所有文件
        for filename in txt_files:
            file_path = os.path.join(data_folder, filename)
            print(f"\n正在处理: {filename}")
            
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 上传到知识库
                result = self.upload_by_str(content, filename)
                
                # 记录结果
                if result == "上传成功":
                    results["success"].append(filename)
                    print(f"✓ {filename}: {result}")
                elif "[跳过]" in result:
                    results["skipped"].append(filename)
                    print(f"⊘ {filename}: {result}")
                else:
                    results["failed"].append(filename)
                    print(f"✗ {filename}: {result}")
                    
            except Exception as e:
                results["failed"].append(filename)
                print(f"✗ {filename}: 读取或上传失败 - {str(e)}")
        
        # 打印统计信息
        print("\n" + "=" * 60)
        print("上传完成！统计信息：")
        print(f"  成功: {len(results['success'])} 个")
        print(f"  跳过: {len(results['skipped'])} 个")
        print(f"  失败: {len(results['failed'])} 个")
        
        return results


# ==================== 测试入口 ====================

if __name__ == '__main__':
    """
    模块测试入口
    
    测试内容：
    1. 批量上传data文件夹文件
    2. 测试单文件上传
    3. 测试重复上传（应该被跳过）
    4. 测试查询功能
    5. 测试清空功能（可选）
    """
    
    # 创建知识库服务实例
    server = KnowledgeBaseService()
    
    # 1. 批量上传data文件夹
    print("\n" + "=" * 60)
    print("1. 批量上传data文件夹文件到知识库")
    print("=" * 60)
    upload_results = server.upload_data_folder()
    
    # 2. 测试单文件上传
    print("\n" + "=" * 60)
    print("2. 测试单文件上传")
    print("=" * 60)
    test_content = "这是测试内容，用于测试单文件上传功能。"
    test_result = server.upload_by_str(test_content, "test_upload.txt")
    print(f"单文件上传结果: {test_result}")
    
    # 3. 测试重复上传
    print("\n" + "=" * 60)
    print("3. 测试重复上传")
    print("=" * 60)
    test_result_duplicate = server.upload_by_str(test_content, "test_upload.txt")
    print(f"重复上传结果: {test_result_duplicate}")
    
    # 4. 测试查询功能
    print("\n" + "=" * 60)
    print("4. 测试查询知识库")
    print("=" * 60)
    queries = [
        "我身高1.66米，尺码推荐",
        "羊绒衫如何洗涤",
        "春季服装颜色推荐"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        results = server.query_knowledge_base(query, k=2)
        for i, doc in enumerate(results):
            print(f"\n  结果 {i+1}:")
            print(f"  来源: {doc.metadata['source']}")
            print(f"  内容: {doc.page_content[:150]}...")
