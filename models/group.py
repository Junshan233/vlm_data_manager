from typing import List, Dict, Any
import json
from datetime import datetime

class DatasetGroup:
    def __init__(self, 
                 id: int, 
                 name: str, 
                 dataset_ids_json: str,
                 create_time: str):
        self.id = id
        self.name = name
        self._dataset_ids_json = dataset_ids_json
        self.create_time = create_time

    @property
    def dataset_ids(self) -> List[int]:
        """获取数据集ID列表"""
        try:
            return json.loads(self._dataset_ids_json)
        except json.JSONDecodeError:
            return []

    @dataset_ids.setter
    def dataset_ids(self, value: List[int]):
        """设置数据集ID列表"""
        if not isinstance(value, list):
            raise ValueError("数据集ID必须是列表")
        if not all(isinstance(x, int) for x in value):
            raise ValueError("所有数据集ID必须是整数")
        self._dataset_ids_json = json.dumps(value)

    def validate(self) -> bool:
        """验证分组属性是否有效"""
        if not self.name:
            return False
        if not self.dataset_ids:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """将分组转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "dataset_ids": self.dataset_ids,
            "create_time": self.create_time
        }

    @classmethod
    def from_tuple(cls, data_tuple: tuple):
        """从数据库元组创建DatasetGroup实例"""
        return cls(*data_tuple)
