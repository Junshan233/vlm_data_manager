from typing import List, Optional
import json
from utils.database import get_db_connection, clear_datasets_cache

class DatasetService:
    @staticmethod
    def get_all_datasets() -> List[tuple]:
        """获取所有数据集元信息，使用database层的缓存"""
        from utils.database import load_all_datasets
        return load_all_datasets()

    @staticmethod
    def get_datasets_by_tags(tags: List[str]) -> List[tuple]:
        """根据标签筛选数据集"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, path, upload_time, tags, data_type, root_path, item_count, "
            "text_count, single_image_count, multi_image_count, video_count FROM datasets"
        )
        
        filtered_datasets = []
        for ds in cursor.fetchall():
            ds_tags = json.loads(ds[4])  # tags_json 在索引4
            if any(tag in ds_tags for tag in tags):
                filtered_datasets.append(ds)
        return filtered_datasets

    @staticmethod
    def update_dataset_tags(dataset_id: int, tags: List[str]) -> bool:
        """更新数据集标签"""
        try:
            from utils.database import update_tags
            update_tags(dataset_id, tags)
            return True
        except Exception as e:
            print(f"更新标签失败: {str(e)}")
            return False

    @staticmethod
    def get_all_unique_tags() -> List[str]:
        """获取所有唯一标签列表"""
        from utils.database import get_all_unique_tags
        return get_all_unique_tags()

    @staticmethod
    def clear_cache():
        """清除数据集相关缓存"""
        from utils.database import clear_datasets_cache
        clear_datasets_cache()

    @staticmethod
    def import_jsonl_dataset(name: str, root_path: str, jsonl_path: str, progress_callback=None) -> tuple[bool, str, int]:
        """导入单个JSONL格式数据集，返回(成功状态, 消息, 数据集ID)"""
        from utils.dataset import import_jsonl_dataset as _import_jsonl
        return _import_jsonl(name, root_path, jsonl_path, progress_callback)

    @staticmethod
    def batch_import_datasets(config: dict, progress_callback=None) -> tuple[bool, str, list[int]]:
        """批量导入多个数据集
        返回值:
            tuple[bool, str, list[int]]: (是否成功, 消息, 成功导入的数据集ID列表)
        """
        from utils.dataset import batch_import_datasets as _batch_import
        return _batch_import(config, progress_callback)

    @staticmethod
    def get_dataset_names() -> List[tuple]:
        """获取数据集ID和名称列表"""
        from utils.database import get_dataset_names
        return get_dataset_names()

    @staticmethod
    def get_dataset_details(dataset_id: int) -> Optional[tuple]:
        """获取数据集详细信息"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, path, tags, root_path FROM datasets WHERE id = ?",
            (dataset_id,)
        )
        return cursor.fetchone()

    @staticmethod
    def update_dataset(dataset_id: int, path: str = None, root_path: str = None, tags: List[str] = None) -> bool:
        """更新数据集信息"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if path is not None:
                updates.append("path = ?")
                params.append(path)
            
            if root_path is not None:
                updates.append("root_path = ?")
                params.append(root_path)
            
            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags, ensure_ascii=False))
            
            if not updates:
                return False
                
            query = f"UPDATE datasets SET {', '.join(updates)} WHERE id = ?"
            params.append(dataset_id)
            
            cursor.execute(query, params)
            conn.commit()
            DatasetService.clear_cache()
            return True
        except Exception as e:
            print(f"更新数据集失败: {str(e)}")
            return False
