import os

# 数据库配置 - 优先从环境变量读取，没有则使用默认值
DB_PATH = os.getenv("DATABASE_URL", "metadata.db")
UPLOAD_DIR = os.getenv("UPLOAD_FOLDER", "../uploads")
ITEMS_PER_PAGE = 4

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
