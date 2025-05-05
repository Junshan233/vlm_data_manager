import streamlit as st

def show_home():
    st.title("多模态数据管理平台")
    st.write("欢迎使用多模态数据管理平台！")
    st.write("请从侧边栏导航栏选择功能页面")

def setup_navigation():

    # 设置导航页面组
    pages = {
        "主菜单": [
            st.Page(show_home, title="首页", icon="🏠", default=True),
        ],
        "数据管理": [
            st.Page("../pages/1_数据集列表.py", title="数据集列表", icon="📋"),
            st.Page("../pages/2_导入数据集.py", title="导入数据集", icon="📤"),
            st.Page("../pages/3_预览数据集.py", title="预览数据集", icon="👁️"),
            st.Page("../pages/4_编辑数据集.py", title="编辑数据集", icon="✏️"),
            st.Page("../pages/5_分组管理.py", title="分组管理", icon="📑"),
        ]
    }

    # 使用 st.navigation 配置导航
    pg = st.navigation(pages)
    pg.run()
