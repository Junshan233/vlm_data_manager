# 多模态数据管理平台

## 项目描述

一个用于管理和预览多模态数据集的Web应用平台，支持文本、图片和视频等多种数据类型。系统提供了友好的Web界面，允许用户导入、预览、管理和标记数据集，帮助用户高效地组织和查看多模态数据。

### 核心功能
- **数据集管理**：导入、编辑、预览和删除数据集
- **分组管理**：创建、编辑和删除数据集分组
- **标签管理**：为数据集添加和删除标签
- **数据预览**：支持文本、图片和视频的在线预览
- **批量操作**：支持批量导入数据集
- **分页展示**：大数据集分页预览

## 安装指南

### 环境要求
- Python 3.8+
- SQLite 3

### 安装步骤
1. 克隆仓库：
```bash
git clone https://github.com/your-repo/vlm_data_platform.git
cd vlm_data_platform
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
export PYTHONPATH=./${PYTHONPATH}
streamlit run app/main.py
```

4. 访问浏览器中显示的URL（通常是 http://localhost:8501）

## 使用说明

### 数据集操作
1. **导入数据集**：
   - 在"导入数据集"页面输入数据集名称
   - 指定根目录路径和JSONL数据文件路径
   - 系统会自动识别数据类型并计算数据量

2. **预览数据集**：
   - 在"数据集列表"页面点击数据集名称
   - 分页浏览数据项（每页显示4个）
   - 支持显示对话、图片和视频内容

3. **编辑数据集**：
   - 修改数据文件路径和根目录路径
   - 管理数据集标签（添加、删除）

## 配置选项

### 通过环境变量配置
创建`.env`文件或在系统环境变量中设置：
```ini
DATABASE_URL=your_db_path.db
UPLOAD_FOLDER=your_upload_path
```

### 默认配置
- `DATABASE_URL`: 默认为"metadata.db"
- `UPLOAD_FOLDER`: 默认为"../uploads"

### 其他配置
编辑`config.py`可修改以下设置：
- 分页大小(ITEMS_PER_PAGE)
- 确保上传目录自动创建

## 贡献指南

欢迎通过以下方式贡献项目：
1. 提交Issue报告问题或建议
2. 创建Pull Request贡献代码
3. 改进文档

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 为重要函数添加docstring

## 许可证

本项目采用 [MIT License](LICENSE)。

## 致谢

- Streamlit - 用于构建Web界面
- SQLite - 轻量级数据库
- python-dotenv - 环境变量管理
- 所有贡献者和用户

## 系统架构

```
+------------------------------+
|       Streamlit App         |
|  （上传、预览、下载、管理） |
+--------------+---------------+
               |
       +-------v--------+
       | SQLite 元数据  |
       | （dataset 名称、|
       |  文件路径、schema）|
       +-------+--------+
               |
       +-------v--------+
       | 本地文件系统   |
       | （./uploads/）  |
       +----------------+
```

## 数据格式

数据基于ShareGPT格式扩展，支持四种类型：
1. 纯文本
2. 单图
3. 多图
4. 视频

示例格式：
```json
{
    "id": 0,
    "conversations": [
        {"from": "human", "value": "用户输入"},
        {"from": "gpt", "value": "助手输出"}
    ],
    "image": ["path/to/image.jpg"],
    "video": ["path/to/video.mp4"]
}
```

## 未来计划
1. 添加数据集导出功能
2. 支持更多数据格式
3. 增强数据可视化
4. 改进搜索和过滤功能
