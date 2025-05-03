import os
import json
import shutil
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------- #
# 常量定义
# ---------------------------------------------------------------------------- #
DB_PATH = "metadata.db"            # SQLite 数据库文件路径
UPLOAD_DIR = "uploads"             # 本地上传文件存储根目录
ITEMS_PER_PAGE = 4                  # 预览每页显示条目数

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------- #
# 数据库初始化与连接
# ---------------------------------------------------------------------------- #
@st.cache_resource
def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    初始化并返回 SQLite 数据库连接，使用 Streamlit 单例缓存保证全局唯一。
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            data_type TEXT NOT NULL,
            content_path TEXT NOT NULL,
            root_path TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

conn = get_db_connection()

# ---------------------------------------------------------------------------- #
# 辅助函数
# ---------------------------------------------------------------------------- #
def get_data_type(item: dict) -> str:
    """
    根据 JSON item 中的字段判断数据类型。
    返回值: 'video' | 'multi-image' | 'single-image' | 'text'
    """
    if 'video' in item and item['video']:
        return 'video'
    if 'images' in item and item['images']:
        return 'multi-image' if len(item['images']) > 1 else 'single-image'
    return 'text'

@st.cache_data
def load_all_datasets() -> list:
    """
    从数据库读取所有数据集元信息，返回列表
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, path, upload_time, tags, data_type, content_path, root_path FROM datasets"
    )
    return cursor.fetchall()


def update_tags(dataset_id: int, tags: list) -> None:
    """
    更新指定数据集的标签字段。
    参数:
      - dataset_id: 数据集主键
      - tags: 标签列表（Python list），会被序列化为 JSON 存储
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE datasets SET tags = ? WHERE id = ?",
        (json.dumps(tags, ensure_ascii=False), dataset_id)
    )
    conn.commit()


def import_jsonl_dataset(dataset_name: str, root_path: str, data_path: str) -> tuple:
    """
    导入 JSONL 格式数据集：
      1. 读取 JSONL 文件
      2. 校验文件非空
      3. 根据第一条记录推断数据类型
      4. 将 JSONL 文件复制到 uploads 目录
      5. 将元信息写入 SQLite
    返回值: (成功标志: bool, 提示消息: str)
    """
    if not os.path.isfile(data_path):
        return False, "数据文件不存在，请检查路径"

    # 创建数据集专属目录
    dataset_dir = os.path.join(UPLOAD_DIR, dataset_name)
    os.makedirs(dataset_dir, exist_ok=True)

    # 读取并解析 JSONL
    items = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            try:
                item = json.loads(line.strip())
                items.append(item)
            except json.JSONDecodeError:
                return False, f"第 {idx+1} 行 JSON 解析失败"

    if not items:
        return False, "数据文件为空，导入失败"

    # 推断数据类型
    data_type = get_data_type(items[0])

    # 复制原始 JSONL 文件
    new_data_filename = os.path.basename(data_path)
    new_data_path = os.path.join(dataset_dir, new_data_filename)
    shutil.copy2(data_path, new_data_path)

    # 写入数据库，仅保留 content_path，避免将大数据存入 SQLite
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO datasets (name, path, upload_time, tags, data_type, content_path, root_path)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            dataset_name,
            new_data_path,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            '[]',
            data_type,
            new_data_path,
            root_path,
        )
    )
    conn.commit()

    return True, "数据集导入成功"


def preview_dataset(dataset_id: int, page: int = 0) -> int:
    """
    在前端预览指定数据集的内容。
    支持文本、图片、视频展示，并提供分页功能。
    返回新页码: int
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content_path, data_type, root_path FROM datasets WHERE id = ?",
        (dataset_id,)
    )
    row = cursor.fetchone()
    if not row:
        st.error("未找到对应数据集")
        return page

    content_path, data_type, root_path = row
    with open(content_path, 'r', encoding='utf-8') as f:
        items = [json.loads(line) for line in f]

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    # 遍历当前页数据项
    for item in items[start:end]:
        st.markdown("---")
        st.write(f"**ID:** {item.get('id')}")
        for conv in item.get('conversations', []):
            prefix = "👤 User:" if conv['from']=='human' else "🤖 Assistant:"
            st.write(prefix, conv['value'])

        # 渲染图片
        for idx, img in enumerate(item.get('images', [])):
            abs_path = os.path.join(root_path, img)
            if os.path.exists(abs_path):
                st.image(abs_path, caption=f"图片 {idx+1}")

        # 渲染视频
        for vid in item.get('video', []):
            abs_path = os.path.join(root_path, vid)
            if os.path.exists(abs_path):
                st.video(abs_path)

    # 分页按钮
    cols = st.columns(2)
    if page > 0 and cols[0].button("上一页", key=f"prev_{dataset_id}"):
        return page - 1
    if end < len(items) and cols[1].button("下一页", key=f"next_{dataset_id}"):
        return page + 1

    return page

# ---------------------------------------------------------------------------- #
# Streamlit 页面布局
# ---------------------------------------------------------------------------- #
st.set_page_config(page_title="多模态数据管理平台", layout="wide")
st.title("多模态数据管理平台")

# 主导航: 数据集列表 / 导入数据集
tabs = st.tabs(["数据集列表", "导入数据集"])

with tabs[0]:
    st.header("所有数据集")
    datasets = load_all_datasets()
    if not datasets:
        st.info("当前尚无数据集，请前往“导入数据集”页面添加。")
    else:
        for ds in datasets:
            ds_id, name, path, upload_time, tags_json, data_type, content_path, root_path = ds
            tags = json.loads(tags_json)

            with st.expander(f"{name} (上传: {upload_time}, 类型: {data_type}, 数量: {sum(1 for _ in open(content_path))} 条)"):
                # 标签管理
                st.write("**标签:**", ", ".join([f"#{t}" for t in tags]) or "无")
                new_tag = st.text_input("添加标签并回车", key=f"tag_in_{ds_id}")
                if new_tag:
                    if new_tag not in tags:
                        tags.append(new_tag)
                        update_tags(ds_id, tags)
                        st.experimental_rerun()

                # 删除标签
                for t in tags:
                    if st.button(f"删除 #{t}", key=f"del_{ds_id}_{t}"):
                        tags.remove(t)
                        update_tags(ds_id, tags)
                        st.experimental_rerun()

                # 预览
                if st.button("预览数据", key=f"view_{ds_id}"):
                    st.session_state[f"page_{ds_id}"] = 0
                if f"page_{ds_id}" in st.session_state:
                    cur_page = st.session_state[f"page_{ds_id}"]
                    new_page = preview_dataset(ds_id, cur_page)
                    if new_page != cur_page:
                        st.session_state[f"page_{ds_id}"] = new_page
                        st.experimental_rerun()

with tabs[1]:
    st.header("导入新数据集")
    ds_name = st.text_input("数据集名称", help="自定义唯一名称，用于区分不同数据集")
    root_path = st.text_input("根目录路径", help="图片和视频的根目录绝对路径")
    data_path = st.text_input("JSONL 文件路径", help="符合格式要求的 .jsonl 文件绝对路径")

    if st.button("开始导入"):
        if not all([ds_name, root_path, data_path]):
            st.error("请填写完整的信息后再导入")
        else:
            ok, msg = import_jsonl_dataset(ds_name, root_path, data_path)
            if ok:
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)
