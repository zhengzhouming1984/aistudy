import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from datetime import datetime

# 知识库服务模块
# 功能：提供知识库的管理、文件上传和清空等功能


# 缓存已处理的MD5值，提高查询效率
_md5_cache = set()
_md5_cache_loaded = False

def _load_md5_cache():
    """
    加载MD5缓存
    """
    global _md5_cache, _md5_cache_loaded
    if not _md5_cache_loaded and os.path.exists(config.md5_path):
        with open(config.md5_path, 'r', encoding='utf-8') as f:
            _md5_cache = set(line.strip() for line in f if line.strip())
        _md5_cache_loaded = True

def check_md5(md5_str: str) -> bool:
    """
    检查md5_str是否已经处理过

    Args:
        md5_str: 要检查的MD5字符串

    Returns:
        bool: False表示MD5未处理过，True表示已经处理过
    """
    if not os.path.exists(config.md5_path):
        # 文件不存在，创建空文件并返回False
        with open(config.md5_path, 'w', encoding='utf-8') as f:
            pass
        return False

    # 加载MD5缓存
    _load_md5_cache()
    
    # 在缓存中查找，时间复杂度O(1)
    return md5_str in _md5_cache


def save_md5(md5_str: str):
    """
    将传入的md5字符串记录到文件内保存

    Args:
        md5_str: 要保存的MD5字符串
    """
    print(f"MD5文件路径: {config.md5_path}")
    # 确保文件存在
    if not os.path.exists(config.md5_path):
        with open(config.md5_path, 'w', encoding='utf-8') as f:
            pass
        print(f"创建了MD5文件: {config.md5_path}")
    # 先检查MD5是否已经存在，避免重复记录
    if not check_md5(md5_str):
        # 使用追加模式打开文件
        with open(config.md5_path, 'a', encoding='utf-8') as f:
            f.write(md5_str + "\n")
            f.flush()  # 确保内容立即写入文件
        print(f"MD5 {md5_str} 已保存")
        # 验证写入是否成功
        with open(config.md5_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"写入后MD5文件内容: '{content}'")
        # 更新缓存
        global _md5_cache
        _md5_cache.add(md5_str)
    else:
        print(f"MD5 {md5_str} 已存在，跳过保存")


def get_string_md5(input_str: str, encoding: str = 'utf-8') -> str:
    """
    将传入的字符串转换为md5字符串

    Args:
        input_str: 要转换的字符串
        encoding: 字符串编码，默认为 'utf-8'

    Returns:
        str: 转换后的md5字符串
    """
    # 将字符串转换为bytes字节数组
    str_bytes = input_str.encode(encoding=encoding)
    # 创建md5对象并计算哈希值
    return hashlib.md5(str_bytes).hexdigest()

from langchain_openai import OpenAIEmbeddings

qwen_embeddings = OpenAIEmbeddings(
    api_key=config.openai_api_key,
    base_url=config.openai_base_url,
    model=config.embedding_model
)


class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.chroma_path,exist_ok=True)
        self.chroma = Chroma(
            collection_name=config.knowledge_base,
            embedding_function=qwen_embeddings,
            persist_directory=config.chroma_path,

        )  # 向量存储的实例Chroma向量库对象

        # 根据配置选择文本分割器
        if config.semantic_chunking:
            # 使用语义切片
            self.spliter = SemanticChunker(qwen_embeddings)
            print("使用语义切片器")
        else:
            # 使用传统的递归字符切片
            self.spliter = RecursiveCharacterTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                length_function=config.length_function,
                separators=config.separators,
                keep_separator=True,
            )
            print("使用递归字符切片器")

    def upload_by_str(self, data: str, filename: str) -> str:
        """
        将传入的字符串，进行向量化，存入向量数据库中
        """
        # 1. 计算 MD5
        md5_hex = get_string_md5(data)

        # 2. 检查是否已存在
        if check_md5(md5_hex):
            return "[跳过]内容已经存在知识库中"

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

            # 4. 入库
            metadata = {
                "source": filename,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "zhengzhouming",
            }

            self.chroma.add_texts(
                knowledge_chunks,
                metadatas=[{**metadata, "chunk_idx": i} for i in range(len(knowledge_chunks))],
            )

            # 5. 成功后再记录 MD5（避免失败却标记成功）
            save_md5(md5_hex)
            return "上传成功"

        except Exception as e:
            # 异常不写 MD5，保证一致性
            return f"[失败]上传异常: {str(e)}"
            
    # 检查 knowledge_base.py 文件中的 clear_knowledge_base 方法
    def clear_knowledge_base(self) -> str:
        """
        清空向量数据库中的所有内容和MD5记录

        Returns:
            str: 清空操作的状态
        """
        try:
            # 清空向量数据库
            documents = self.chroma.get()
            if documents['ids']:
                self.chroma.delete(ids=documents['ids'])
                print(f"已删除 {len(documents['ids'])} 个文档")

            # 打印MD5文件路径
            print(f"MD5文件路径: {config.md5_path}")

            # 清空MD5记录文件
            with open(config.md5_path, 'w', encoding='utf-8') as f:
                f.write('')
            print("MD5文件已清空")

            # 验证MD5文件是否为空
            with open(config.md5_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"清空后MD5文件内容: '{content}'")

            return "知识库和MD5记录已清空"
        except Exception as e:
            print(f"清空知识库失败: {str(e)}")
            return f"清空知识库失败: {str(e)}"

    def query_knowledge_base(self, query: str, k: int = 2) -> list:
        """
        查询向量数据库中的相关文档

        Args:
            query: 查询字符串
            k: 返回结果数量，默认为 2

        Returns:
            list: 相关文档列表
        """
        try:
            # 使用 Chroma 的相似度搜索功能
            docs = self.chroma.similarity_search(query, k=k)
            return docs
        except Exception as e:
            print(f"查询知识库失败: {str(e)}")
            return []

if __name__ == '__main__':    # 测试get_string_md5函数
    # 测试get_string_md5函数
    test_str = "hello world"
    test_str1 = "hello world"
    test_str2 = "hello world!"

    server = KnowledgeBaseService()
    print(server.upload_by_str(test_str, "md5.txt"))
    print(server.upload_by_str(test_str1, "md5.txt"))
    print(server.upload_by_str(test_str2, "md5.txt"))

# 查询知识库
    results = server.query_knowledge_base("我的体重110斤，身高1米66，尺码推荐", k=2)

# 打印结果
    for doc in results:
        print(f"文档来源: {doc.metadata['source']}")
        print(f"文档内容: {doc.page_content}")
        print(f"创建时间: {doc.metadata['create_time']}")
        print(f"操作人: {doc.metadata['operator']}")
        print("-----"*10)
    
    # print(server.clear_knowledge_base())
