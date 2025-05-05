from typing import List, Tuple, Optional
import json
from datetime import datetime
from utils.database import get_db_connection

class GroupService:
    @staticmethod
    def create_dataset_group(name: str, dataset_ids: List[int]) -> Tuple[bool, str]:
        """创建新的数据集分组"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查分组名称是否已存在
            cursor.execute("SELECT name FROM dataset_groups WHERE name = ?", (name,))
            if cursor.fetchone():
                return False, "分组名称已存在"
            
            # 创建新分组
            cursor.execute(
                "INSERT INTO dataset_groups (name, dataset_ids, create_time) VALUES (?, ?, ?)",
                (name, json.dumps(dataset_ids), datetime.now().isoformat())
            )
            conn.commit()
            return True, "分组创建成功"
        except Exception as e:
            return False, f"创建分组失败: {str(e)}"

    @staticmethod
    def get_all_groups() -> List[Tuple]:
        """获取所有分组信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, dataset_ids, create_time FROM dataset_groups")
        return cursor.fetchall()

    @staticmethod
    def get_group_datasets(group_id: int) -> Optional[List[int]]:
        """获取分组中的数据集ID列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT dataset_ids FROM dataset_groups WHERE id = ?", (group_id,))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

    @staticmethod
    def update_group_datasets(group_id: int, dataset_ids: List[int]) -> bool:
        """更新分组中的数据集"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE dataset_groups SET dataset_ids = ? WHERE id = ?",
                (json.dumps(dataset_ids), group_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"更新分组失败: {str(e)}")
            return False

    @staticmethod
    def get_group_details(group_id: int) -> Optional[dict]:
        """获取分组详细信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, dataset_ids, create_time FROM dataset_groups WHERE id = ?",
            (group_id,)
        )
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "dataset_ids": json.loads(result[2]),
                "create_time": result[3]
            }
        return None

    @staticmethod
    def delete_dataset_group(group_id: int) -> Tuple[bool, str]:
        """删除数据集分组"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dataset_groups WHERE id = ?", (group_id,))
            conn.commit()
            return True, "分组删除成功"
        except Exception as e:
            return False, f"删除分组失败: {str(e)}"

    @staticmethod
    def export_group_info(group_id: int) -> Optional[dict]:
        """导出分组信息"""
        group = GroupService.get_group_details(group_id)
        if not group:
            return None
            
        from services.dataset_service import DatasetService
        datasets = []
        for ds_id in group["dataset_ids"]:
            ds = DatasetService.get_dataset_details(ds_id)
            if ds:
                datasets.append({
                    "id": ds[0],
                    "name": ds[1],
                    "path": ds[2],
                    "root_path": ds[4]
                })
        
        return {
            "group_id": group["id"],
            "group_name": group["name"],
            "create_time": group["create_time"],
            "datasets": datasets
        }

    @staticmethod
    def get_group_stats(group_id: int) -> dict:
        """获取分组统计数据"""
        group = GroupService.get_group_details(group_id)
        if not group:
            return {}
            
        # 获取分组内所有数据集的基础计数
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['?']*len(group["dataset_ids"]))
        query = f"""
            SELECT
                name, item_count, text_count,
                single_image_count, multi_image_count,
                video_count
            FROM datasets
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, group["dataset_ids"])
        rows = cursor.fetchall()
        
        # 计算统计指标
        stats = {
            'total': 0,
            'text': 0,
            'single_image': 0,
            'multi_image': 0,
            'video': 0,
            'datasets': {}
        }
        
        for name, total, text, single, multi, video in rows:
            stats['total'] += total or 0
            stats['text'] += text or 0
            stats['single_image'] += single or 0
            stats['multi_image'] += multi or 0
            stats['video'] += video or 0
            stats['datasets'][name] = total or 0
            
        return stats

    @staticmethod
    def clear_groups_cache():
        """清除分组相关缓存"""
        from utils.group import clear_groups_cache
        clear_groups_cache()
