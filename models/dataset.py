from typing import List, Dict, Any
import json

class Dataset:
    def __init__(self, 
                 id: int, 
                 name: str, 
                 path: str, 
                 upload_time: str,
                 tags_json: str,
                 data_type: str,
                 root_path: str,
                 item_count: int = 0):
        self.id = id
        self.name = name
        self.path = path
        self.upload_time = upload_time
        self._tags_json = tags_json
        self.data_type = data_type
        self.root_path = root_path
        self.item_count = item_count

    @property
    def tags(self) -> List[str]:
        """获取标签列表"""
        try:
            return json.loads(self._tags_json)
        except json.JSONDecodeError:
            return []

    @tags.setter
    def tags(self, value: List[str]):
        """设置标签列表"""
        if not isinstance(value, list):
            raise ValueError("标签必须是列表")
        self._tags_json = json.dumps(value, ensure_ascii=False)

    def validate(self) -> bool:
        """验证数据集属性是否有效"""
        if not self.name:
            return False
        if not self.path:
            return False
        if not self.data_type:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """将数据集转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "upload_time": self.upload_time,
            "tags": self.tags,
            "data_type": self.data_type,
            "root_path": self.root_path,
            "item_count": self.item_count
        }

    @classmethod
    def from_tuple(cls, data_tuple: tuple):
        """从数据库元组创建Dataset实例"""
        return cls(*data_tuple)
