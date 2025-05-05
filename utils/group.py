import json
from datetime import datetime
import streamlit as st
from .database import get_db_connection, clear_datasets_cache

@st.cache_data
def get_all_groups() -> list:
    """获取所有数据集分组信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, dataset_ids, create_time FROM dataset_groups")
    return cursor.fetchall()

def get_group_details(group_id: int) -> dict:
    """获取指定分组的详细信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, dataset_ids, create_time FROM dataset_groups WHERE id = ?",
        (group_id,)
    )
    group = cursor.fetchone()
    if not group:
        return None
    
    group_id, name, dataset_ids_json, create_time = group
    dataset_ids = json.loads(dataset_ids_json)
    
    return {
        "id": group_id,
        "name": name,
        "dataset_ids": dataset_ids,
        "create_time": create_time
    }

def create_dataset_group(name: str, dataset_ids: list) -> tuple:
    """
    创建新的数据集分组
    返回值: (成功标志: bool, 提示消息: str)
    """
    if not name:
        return False, "分组名称不能为空"
    
    if not dataset_ids:
        return False, "分组必须包含至少一个数据集"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查名称是否已存在
    cursor.execute("SELECT id FROM dataset_groups WHERE name = ?", (name,))
    if cursor.fetchone():
        return False, f"分组名称 '{name}' 已存在"
    
    # 创建新分组
    cursor.execute(
        "INSERT INTO dataset_groups (name, dataset_ids, create_time) VALUES (?, ?, ?)",
        (
            name,
            json.dumps(dataset_ids),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()
    
    # 清除相关缓存
    get_all_groups.clear()
    
    return True, f"分组 '{name}' 创建成功"

def delete_dataset_group(group_id: int) -> tuple:
    """
    删除指定的数据集分组
    返回值: (成功标志: bool, 提示消息: str)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM dataset_groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()
    
    if not group:
        return False, "指定的分组不存在"
    
    cursor.execute("DELETE FROM dataset_groups WHERE id = ?", (group_id,))
    conn.commit()
    
    # 清除相关缓存
    get_all_groups.clear()
    
    return True, f"分组 '{group[0]}' 已删除"

def export_group_info(group_id: int) -> dict:
    """
    导出分组信息为JSON格式
    返回包含数据集信息的字典
    """
    group = get_group_details(group_id)
    if not group:
        return None
    
    dataset_ids = group["dataset_ids"]
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = {}
    for ds_id in dataset_ids:
        cursor.execute(
            "SELECT name, path, root_path, item_count FROM datasets WHERE id = ?",
            (ds_id,)
        )
        ds = cursor.fetchone()
        if ds:
            name, annotation_path, root_path, length = ds
            result[name] = {
                "root": root_path,
                "annotation": annotation_path,
                "length": length
            }
    
    return result

def clear_groups_cache():
    """清除分组相关缓存"""
    get_all_groups.clear()
