#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库文件上传Web应用

这是一个使用 Streamlit 构建的文件上传和管理Web应用，用于：
1. 上传TXT文件到知识库
2. 批量上传data文件夹文件
3. 查看知识库状态
4. 清空知识库
5. 测试知识库功能（单文件上传、查询）

使用方法：
    streamlit run app_file_uploader.py

然后在浏览器中访问生成的本地URL
"""

import streamlit as st
from knowledge_base import KnowledgeBaseService
import os
import time
import config_data as config


# ==================== 页面配置 ====================

# 设置网页标题
st.title("📚 知识库更新服务")

# 页面描述
st.markdown("""
本应用用于管理知识库，支持以下功能：
- 📤 上传TXT文件到知识库
- 📁 批量上传data文件夹文件
- 📊 查看知识库状态
- 🗑️ 清空知识库
- 🧪 测试知识库功能
""")


# ==================== 初始化 ====================

# 在session_state中保存知识库服务实例
# 避免每次页面刷新都重新初始化
if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()
    st.success("✅ 知识库服务初始化成功！")


# ==================== 状态显示函数 ====================

def display_knowledge_base_status():
    """
    显示当前知识库状态
    
    显示信息包括：
    - 知识库中的文档数量
    - 已处理的MD5记录数量（用于去重）
    """
    try:
        # 获取知识库中的文档数量
        documents = st.session_state["service"].chroma.get()
        doc_count = len(documents['ids']) if documents and 'ids' in documents else 0
        
        # 显示文档数量
        st.metric("📄 知识库文档数量", doc_count)
        
        # 显示MD5记录数量
        if os.path.exists(config.md5_path):
            with open(config.md5_path, 'r', encoding='utf-8') as f:
                md5_count = len([line for line in f if line.strip()])
            st.metric("🔍 已处理MD5记录", md5_count)
        else:
            st.metric("🔍 已处理MD5记录", 0)
            
    except Exception as e:
        st.error(f"❌ 获取知识库状态失败: {str(e)}")


# ==================== 侧边栏 - 知识库状态 ====================

with st.sidebar:
    st.header("📊 知识库状态")
    display_knowledge_base_status()
    
    st.divider()
    
    # 清空知识库按钮
    st.subheader("⚠️ 危险操作")
    if st.button("🗑️ 清空知识库", type="secondary"):
        # 显示确认对话框
        if st.checkbox("我确认要清空知识库（此操作不可恢复）"):
            with st.spinner("正在清空知识库..."):
                result = st.session_state["service"].clear_knowledge_base()
                st.success(result)
                # 延迟刷新页面
                time.sleep(1)
                st.rerun()


# ==================== 主界面 - 文件上传 ====================

st.header("📤 文件上传")

# 创建文件上传器组件
# 参数说明：
# - label: 上传按钮的标签文本
# - type: 允许上传的文件类型，这里只接受txt文件
# - accept_multiple_files: 是否允许多文件上传
uploader_file = st.file_uploader(
    "请选择要上传的TXT文件",
    type=['txt'],
    accept_multiple_files=False,
    help="支持单个TXT文件上传，文件大小限制为10MB"
)

# 处理上传的文件
if uploader_file is not None:
    # 检查文件大小（限制为10MB）
    max_file_size = 10 * 1024 * 1024  # 10MB
    
    if uploader_file.size > max_file_size:
        st.error(f"❌ 文件大小超过限制（最大10MB），当前文件大小: {uploader_file.size / (1024 * 1024):.2f}MB")
    else:
        # 显示文件信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("文件名", uploader_file.name)
        with col2:
            st.metric("文件类型", uploader_file.type or "text/plain")
        with col3:
            st.metric("文件大小", f"{uploader_file.size / 1024:.2f} KB")
        
        # 读取并上传文件内容
        try:
            # 读取文件内容（UTF-8编码）
            text = uploader_file.getvalue().decode("utf-8")
            
            # 显示文件内容预览
            with st.expander("📄 文件内容预览"):
                st.text(text[:1000] + ("..." if len(text) > 1000 else ""))
            
            # 上传按钮
            if st.button("🚀 上传到知识库", type="primary"):
                with st.spinner("正在上传..."):
                    # 添加上传动画
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # 执行上传
                    result = st.session_state["service"].upload_by_str(text, uploader_file.name)
                    
                    # 显示结果
                    if "成功" in result:
                        st.success(f"✅ {result}")
                    elif "跳过" in result:
                        st.info(f"ℹ️ {result}")
                    else:
                        st.error(f"❌ {result}")
                    
                    # 刷新页面显示最新状态
                    time.sleep(1)
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ 文件处理失败: {str(e)}")


# ==================== 批量上传功能 ====================

st.divider()
st.header("📁 批量上传")

if st.button("📂 批量上传data文件夹文件", type="primary"):
    with st.spinner("正在批量上传..."):
        # 执行批量上传
        results = st.session_state["service"].upload_data_folder()
        
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ 成功", len(results['success']))
        with col2:
            st.metric("⏭️ 跳过", len(results['skipped']))
        with col3:
            st.metric("❌ 失败", len(results['failed']))
        
        # 显示详细信息
        if results['success']:
            with st.expander("✅ 成功上传的文件"):
                for file in results['success']:
                    st.write(f"- {file}")
        
        if results['skipped']:
            with st.expander("⏭️ 跳过的文件（已存在）"):
                for file in results['skipped']:
                    st.write(f"- {file}")
        
        if results['failed']:
            with st.expander("❌ 上传失败的文件"):
                for file in results['failed']:
                    st.write(f"- {file}")


# ==================== 测试功能区域 ====================

st.divider()
st.header("🧪 测试功能")

# 使用标签页组织测试功能
tab1, tab2 = st.tabs(["📝 单文件上传测试", "🔍 查询测试"])

# 标签页1：单文件上传测试
with tab1:
    st.subheader("测试单文件上传")
    
    # 测试内容输入
    test_content = st.text_area(
        "测试内容",
        "这是测试内容，用于测试单文件上传功能。",
        height=100
    )
    
    # 测试文件名输入
    test_filename = st.text_input("测试文件名", "test_upload.txt")
    
    # 执行测试按钮
    if st.button("🚀 执行单文件上传测试"):
        with st.spinner("正在上传..."):
            result = st.session_state["service"].upload_by_str(test_content, test_filename)
            
            if "成功" in result:
                st.success(f"✅ {result}")
            elif "跳过" in result:
                st.info(f"ℹ️ {result}")
            else:
                st.error(f"❌ {result}")

# 标签页2：查询测试
with tab2:
    st.subheader("测试查询功能")
    
    # 查询输入
    test_query = st.text_input(
        "测试查询",
        "我身高1.66米，尺码推荐",
        placeholder="输入查询内容..."
    )
    
    # 执行查询按钮
    if st.button("🔍 执行查询测试"):
        with st.spinner("正在查询..."):
            results = st.session_state["service"].query_knowledge_base(test_query, k=2)
            
            # 显示查询结果
            st.write(f"📊 查询到 {len(results)} 个结果：")
            
            for i, doc in enumerate(results):
                with st.expander(f"📄 结果 {i+1}: {doc.metadata.get('source', '未知')}"):
                    st.write(f"**来源：** {doc.metadata.get('source', '未知')}")
                    st.write(f"**创建时间：** {doc.metadata.get('create_time', '未知')}")
                    st.write(f"**操作人：** {doc.metadata.get('operator', '未知')}")
                    st.write(f"**内容：**")
                    st.text(doc.page_content)


# ==================== 页脚 ====================

st.divider()
st.caption("📚 知识库管理系统 | Powered by Streamlit & LangChain")
