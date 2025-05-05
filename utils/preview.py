import json
import os
import html
import streamlit as st
from config import ITEMS_PER_PAGE
from .database import get_db_connection

@st.cache_data
def load_jsonl_lines(file_path: str) -> list:
    """缓存加载JSONL文件的行内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.readlines()

def get_items_for_page(lines: list, start: int, end: int) -> list:
    """只解析指定页面范围内的JSON数据"""
    items = []
    for line in lines[start:end]:
        try:
            items.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            st.error(f"JSON解析错误: {line[:100]}...")
            continue
    return items

def preview_dataset(dataset_id: int, page: int = 0) -> int:
    """
    在前端预览指定数据集的内容。
    支持文本、图片、视频展示，并提供分页功能。
    """
    # 添加自定义 CSS 样式
    st.markdown("""
        <style>
        .chat-message {
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 10px;
            position: relative;
        }
        .human-message {
            background-color: #e5f6ff;
            margin-right: 50px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        .assistant-message {
            background-color: #f0f0f0;
            margin-left: 50px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        .message-header {
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        .message-content {
            font-size: 1rem;
            line-height: 1.5;
        }
        </style>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT path, data_type, root_path FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    row = cursor.fetchone()
    if not row:
        st.error("未找到对应数据集")
        return page

    content_path, data_type, root_path = row
    
    # 使用缓存加载文件内容
    lines = load_jsonl_lines(content_path)
    
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    
    # 只解析当前页面需要的数据
    items = get_items_for_page(lines, start, end)
    total_items = len(lines)

    # 遍历当前页数据项
    for item in items:
        st.markdown("---")
        # 使用卡片容器
        with st.container():
            st.markdown(f"#### 对话 ID: {item.get('id')}")
            
            # 渲染图片
            if 'image' in item:
                images = item['image'] if isinstance(item['image'], list) else [item['image']]
                cols = st.columns(min(len(images), 3))  # 最多3列
                for idx, (img, col) in enumerate(zip(images, cols)):
                    abs_path = os.path.join(root_path, img)
                    if os.path.exists(abs_path):
                        with col:
                            st.image(abs_path, caption=f"图片 {idx+1}", width=400)

            # 渲染视频
            if 'video' in item and item['video']:
                videos = item['video'] if isinstance(item['video'], list) else [item['video']]
                for vid in videos:
                    abs_path = os.path.join(root_path, vid)
                    if os.path.exists(abs_path):
                        st.video(abs_path)

            for conv in item.get('conversations', []):
                is_human = conv['from'] == 'human'
                message_class = 'human-message' if is_human else 'assistant-message'
                icon = "👤" if is_human else "🤖"
                role = "User" if is_human else "Assistant"
                
                # 构建消息HTML
                value = conv['value']
                value = html.escape(value)  # 转义HTML特殊字符
                message_html = f"""
                <div class="chat-message {message_class}">
                    <div class="message-header">
                        {icon} <b>{role}</b>
                    </div>
                    <div class="message-content">
                        {value}
                    </div>
                </div>
                """
                st.markdown(message_html, unsafe_allow_html=True)

    # 分页控制
    if lines:
        total_pages = len(lines) // ITEMS_PER_PAGE + (1 if len(lines) % ITEMS_PER_PAGE > 0 else 0)
        cols = st.columns([1, 3, 1])
        
        with cols[0]:
            if page > 0:
                if st.button("⬅️ 上一页", key=f"prev_{dataset_id}"):
                    return page - 1
                    
        with cols[1]:
            st.markdown(f"<div style='text-align: center'>第 {page + 1} 页，共 {total_pages} 页</div>", unsafe_allow_html=True)
            
        with cols[2]:
            if end < len(lines):
                if st.button("下一页 ➡️", key=f"next_{dataset_id}"):
                    return page + 1

    return page
