import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

# 知识库服务模块
# 功能：提供知识库的管理、文件上传和清空等功能


def check_md5(md5_str: str) -> bool:
    """
    检查传入的md5字符串是否已经被处理过了

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

    # 文件存在，逐行检查
    with open(config.md5_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == md5_str:
                return True

    # 没有找到匹配的MD5
    return False


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

api_key = os.getenv("OPENAI_API_KEY", "sk-fwitbnnwrrapdhijtyprotmhldjakiryyassgadysfombilw")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

qwen_embeddings = OpenAIEmbeddings(
    api_key=api_key,
    base_url=base_url,
    model="Qwen/Qwen3-Embedding-0.6B"
)


class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.chroma_path,exist_ok=True)
        self.chroma = Chroma(
            collection_name=config.knowledge_base,
            embedding_function=qwen_embeddings,
            persist_directory=config.chroma_path,

        )  # 向量存储的实例Chroma向量库对象

        # 修改后
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            length_function=config.length_function,
            separators=config.separators,
            keep_separator=True,
        ) # 文本分割器的对象

    def upload_by_str(self, data: str, filename) -> str:
        """
        将传入的字符串，进行向量化，存入向量数据库中

        Args:
            data: 要上传的字符串内容
            filename: 文件名（作为元数据）

        Returns:
            str: 上传状态
        """
        # 先得到传入字符串的md5值
        md5_hex = get_string_md5(data)
        print(f"计算得到的MD5值: {md5_hex}")

        # 检查MD5文件的内容
        if os.path.exists(config.md5_path):
            with open(config.md5_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            print(f"保存后MD5文件内容: {new_content}")

        if check_md5(md5_hex):
            print(f"MD5值 {md5_hex} 已存在，跳过上传")
            return "[跳过]内容已经存在知识库中"

        # 保存MD5，记录已处理
        save_md5(md5_hex)

        knowledge_chunks: list[str] = self.spliter.split_text(data)

        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "zhengzhouming",
        }

        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )

        return "上传成功"
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

if __name__ == '__main__':    # 测试get_string_md5函数
    # 测试get_string_md5函数
    test_str = "hello world"
    test_str1 = "hello world"
    test_str2 = "hello world!"
    # md5 = get_string_md5(test_str)  # 计算 test_str 的 MD5
    # md51 = get_string_md5(test_str1)  # 计算 test_str1 的 MD5
    # md52 = get_string_md5(test_str2)  # 计算 test_str2 的 MD5
    # print(f"字符串 {test_str} 的MD5值为: {md5}")  # 显示 test_str 的 MD5
    # print(f"字符串 {test_str1} 的MD5值为: {md51}")  # 显示 test_str1 的 MD5
    # print(f"字符串 {test_str2} 的MD5值为: {md52}")  # 显示 test_str2 的 MD5
    #
    # print(check_md5(md5))
    # save_md5(md5)
    # print(check_md5(md51))
    # save_md5(md51)
    # print(check_md5(md52))
    # save_md5(md52)

    server = KnowledgeBaseService()
    print(server.upload_by_str(test_str, "test.txt"))
    print(server.upload_by_str(test_str1, "test.txt"))
    print(server.upload_by_str(test_str2, "test.txt"))

    print(server.clear_knowledge_base())
