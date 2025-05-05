import sqlite3
import json
from datetime import datetime
import streamlit as st
from config import DB_PATH

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
            root_path TEXT NOT NULL,
            item_count INTEGER DEFAULT 0,
            text_count INTEGER DEFAULT 0,
            single_image_count INTEGER DEFAULT 0,
            multi_image_count INTEGER DEFAULT 0,
            video_count INTEGER DEFAULT 0
        )
    """)
    # 创建数据集分组表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dataset_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dataset_ids TEXT NOT NULL,
            create_time TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

@st.cache_data
def load_all_datasets() -> list:
    """
    从数据库读取所有数据集元信息，返回列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, path, upload_time, tags, data_type, root_path, item_count, "
        "text_count, single_image_count, multi_image_count, video_count FROM datasets"
    )
    return cursor.fetchall()

@st.cache_data
def get_dataset_names() -> list:
    """获取所有数据集名称及ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM datasets")
    return cursor.fetchall()

@st.cache_data
def get_all_unique_tags() -> list:
    """
    获取所有数据集中使用过的唯一标签列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tags FROM datasets")
    all_tags = []
    for (tags_json,) in cursor.fetchall():
        tags = json.loads(tags_json)
        all_tags.extend(tags)
    # 返回去重后的标签列表
    return sorted(list(set(all_tags)))

def update_tags(dataset_id: int, tags: list) -> None:
    """
    更新指定数据集的标签字段。
    参数:
      - dataset_id: 数据集主键
      - tags: 标签列表（Python list），会被序列化为 JSON 存储
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE datasets SET tags = ? WHERE id = ?",
        (json.dumps(tags, ensure_ascii=False), dataset_id))
    conn.commit()
    clear_datasets_cache()


def clear_datasets_cache():
    """
    清除数据集相关缓存
    """
    load_all_datasets.clear()
    get_dataset_names.clear()
    get_all_unique_tags.clear()
