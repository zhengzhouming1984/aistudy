#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库更新服务

这是一个使用 Streamlit 构建的文件上传应用，用于上传 TXT 文件到知识库。

功能：
1. 提供文件上传界面，仅接受 TXT 文件
2. 显示上传文件的基本信息（文件名、格式、大小）
3. 显示上传文件的内容

使用方法：
1. 运行命令：streamlit run app_file_uploader.py
2. 在浏览器中访问生成的本地 URL 
3. 点击 "浏览文件" 按钮上传 TXT 文件
4. 查看文件信息和内容
"""

import streamlit as st  # 导入 Streamlit 库，用于构建 Web 应用
from knowledge_base import KnowledgeBaseService
import os
import time  # 导入 time 模块，用于添加延时

# 设置网页标题
st.title("知识库更新服务")

# 创建文件上传器组件
# 参数说明：
# - label: 上传按钮的标签文本
# - type: 允许上传的文件类型，这里只接受 txt 文件
# - accept_multiple_files: 是否允许上传多个文件，False 表示只允许上传一个文件
uploader_file = st.file_uploader(
    "请上传 TXT 文件",
    type=['txt'],  # 限制上传文件类型为 TXT
    accept_multiple_files=False,  # 仅接受单个文件上传
)

if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()

# 显示当前知识库状态
def display_knowledge_base_status():
    """显示当前知识库状态"""
    try:
        # 获取知识库中的文档数量
        documents = st.session_state["service"].chroma.get()
        doc_count = len(documents['ids'])
        st.write(f"当前知识库中的文档数量: {doc_count}")
        
        # 显示MD5记录数量
        import config_data as config
        md5_path = config.md5_path
        if os.path.exists(md5_path):
            with open(md5_path, 'r', encoding='utf-8') as f:
                md5_count = len(f.readlines())
            st.write(f"已处理的MD5记录数量: {md5_count}")
        else:
            st.write("已处理的MD5记录数量: 0")
    except Exception as e:
        st.write(f"获取知识库状态失败: {str(e)}")

# 显示知识库状态
display_knowledge_base_status()

# 在文件顶部添加
if "uploaded" not in st.session_state:
    st.session_state["uploaded"] = False

# 添加清空知识库按钮
if st.button("清空知识库"):
    result = st.session_state["service"].clear_knowledge_base()
    st.write(result)
    print(f"清空结果: {result}")  # 在控制台输出结果
    # 重置上传状态
    st.session_state["uploaded"] = False
    # 刷新页面以显示最新状态
    st.rerun()

# 添加重置上传状态按钮
if st.button("重置上传状态"):
    st.session_state["uploaded"] = False

# 检查是否有文件被上传
if uploader_file is not None:
    try:
        # 检查文件大小（限制为 10MB）
        max_file_size = 10 * 1024 * 1024  # 10MB
        if uploader_file.size > max_file_size:
            st.error(f"文件大小超过限制（最大 10MB），当前文件大小: {uploader_file.size / (1024 * 1024):.2f}MB")
        else:
            # 提取文件的基本信息
            file_name = uploader_file.name  # 获取文件名
            file_type = uploader_file.type  # 获取文件类型
            file_size = uploader_file.size / 1024  # 计算文件大小（单位：KB）
            
            # 显示文件信息
            st.subheader(f"文件名:{file_name}")  # 显示文件名作为子标题
            st.write(f"格式:{file_type}| 大小:{file_size:.2f}KB")  # 显示文件格式和大小

            # 读取文件内容
            # 1. getvalue() 方法获取文件的字节数据
            # 2. decode("utf-8") 将字节数据转换为 UTF-8 编码的字符串
            text = uploader_file.getvalue().decode("utf-8")
            with st.spinner("上传中..."):
                time.sleep(3)
                result = st.session_state["service"].upload_by_str(text,file_name)
                st.write(result)
            print(f"上传结果: {result}")  # 在控制台输出结果
    except Exception as e:
        st.error(f"文件处理失败: {str(e)}")
        print(f"文件处理失败: {str(e)}")
