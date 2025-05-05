import os
import json
import shutil
from datetime import datetime
import streamlit as st
from config import UPLOAD_DIR
from .database import get_db_connection, clear_datasets_cache

def get_data_type(item: dict) -> str:
    """
    根据 JSON item 中的字段判断数据类型。
    返回值: 'video' | 'multi-image' | 'single-image' | 'text'
    """
    if 'video' in item and item['video']:
        return 'video'
    if 'image' in item and item['image']:
        if isinstance(item['image'], str):
            return 'image'
        elif isinstance(item['image'], list):
            return 'multi-image'
    return 'text'

def import_jsonl_dataset(dataset_name: str, root_path: str, data_path: str, progress_fn=None) -> tuple[bool, str, int]:
    """
    导入 JSONL 格式数据集，支持进度回调
    参数:
      - progress_fn: 进度回调函数，接收 (阶段描述: str, 当前进度: float) 两个参数
    """
    if not os.path.isfile(data_path):
        return False, "数据文件不存在，请检查路径", -1

    try:
        if progress_fn:
            progress_fn("正在准备导入...", 0)

        # 检查数据集是否已存在
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM datasets WHERE name = ?", (dataset_name,))
        existing = cursor.fetchone()
        if existing:
            return True, f"数据集{dataset_name}已存在", existing[0]

        # 创建数据集专属目录
        dataset_dir = os.path.join(UPLOAD_DIR, dataset_name)
        os.makedirs(dataset_dir, exist_ok=True)

        if progress_fn:
            progress_fn("正在读取文件...", 0.1)
        
        with open(data_path, 'r', encoding='utf-8') as f:
            datas = f.readlines()

        total_lines = len(datas)

        if progress_fn:
            progress_fn("开始解析数据...", 0.2)

        # 读取并解析 JSONL，显示进度
        items = []
        for idx, line in enumerate(datas):
            try:
                item = json.loads(line.strip())
                items.append(item)
                if progress_fn and idx % 100 == 0:  # 每100行更新一次进度
                    progress = 0.2 + (0.4 * idx / total_lines)  # 0.2-0.6范围内
                    progress_fn(f"正在解析数据... ({idx}/{total_lines})", progress)
            except json.JSONDecodeError:
                return False, f"第 {idx+1} 行 JSON 解析失败", -1

        if not items:
            return False, "数据文件为空，导入失败", -1

        if progress_fn:
            progress_fn("正在推断数据类型...", 0.7)

        # 统计各类型数据数量
        text_count = 0
        single_image_count = 0
        multi_image_count = 0
        video_count = 0
        
        # 遍历所有数据项统计数量
        for item in items:
            data_type = get_data_type(item)
            if data_type == 'video':
                video_count += 1
            elif data_type == 'multi-image':
                multi_image_count += 1
            elif data_type == 'image':
                single_image_count += 1
            else:
                text_count += 1
        
        item_count = len(items)
        # 使用最多的类型作为主要数据类型
        counts = {
            'text': text_count,
            'image': single_image_count,
            'multi-image': multi_image_count,
            'video': video_count
        }
        data_type = max(counts.items(), key=lambda x: x[1])[0]

        if progress_fn:
            progress_fn("正在复制数据文件...", 0.8)

        # 复制原始 JSONL 文件
        new_data_filename = os.path.basename(data_path)
        new_data_path = os.path.join(dataset_dir, new_data_filename)
        shutil.copy2(data_path, new_data_path)

        if progress_fn:
            progress_fn("正在写入数据库...", 0.9)

        # 写入数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO datasets (name, path, upload_time, tags, data_type, root_path, item_count, "
            "text_count, single_image_count, multi_image_count, video_count)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                dataset_name,
                new_data_path,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                '[]',
                data_type,
                root_path,
                item_count,
                text_count,
                single_image_count,
                multi_image_count,
                video_count
            )
        )
        conn.commit()

        if progress_fn:
            progress_fn("导入完成", 1.0)

        return True, "数据集导入成功", cursor.lastrowid
    except Exception as e:
        return False, f"导入过程发生错误: {str(e)}", -1

def batch_import_datasets(config: dict, progress_fn=None) -> tuple[bool, str, list[int]]:
    """
    批量导入数据集，支持总体进度显示
    参数:
      - progress_fn: 进度回调函数，接收 (阶段描述: str, 当前进度: float) 两个参数
    """
    if not isinstance(config, dict):
        return False, "配置格式错误", []
    
    total = len(config)
    success_count = 0
    failed_imports = []
    imported_ids = []
    
    for idx, (ds_name, ds_config) in enumerate(config.items(), 1):
        if progress_fn:
            progress_fn(f"正在导入 {ds_name} ({idx}/{total})", (idx-1)/total)
        
        # 验证配置格式
        if not isinstance(ds_config, dict) or \
           'root' not in ds_config or \
           'annotation' not in ds_config:
            failed_imports.append(f"{ds_name}: 配置格式错误")
            continue
        
        # 定义单个数据集的进度回调
        def single_progress(stage, prog):
            if progress_fn:
                total_prog = ((idx-1) + prog) / total
                progress_fn(f"[{ds_name}] {stage}", total_prog)
        
        # 尝试导入单个数据集
        try:
            ok, msg, ds_id = import_jsonl_dataset(
                ds_name,
                ds_config['root'],
                ds_config['annotation'],
                single_progress
            )
            if ok:
                success_count += 1
                imported_ids.append(ds_id)
            else:
                failed_imports.append(f"{ds_name}: {msg}")
        except Exception as e:
            failed_imports.append(f"{ds_name}: {str(e)}")
    
    if progress_fn:
        progress_fn("导入完成", 1.0)
    
    if failed_imports:
        failed_msg = "\n".join(failed_imports)
        return False, f"批量导入完成，共 {total} 个数据集，成功 {success_count} 个，失败 {len(failed_imports)} 个。\n失败详情：\n{failed_msg}", imported_ids
    else:
        return True, f"批量导入完成，共 {total} 个数据集全部导入成功。", imported_ids
