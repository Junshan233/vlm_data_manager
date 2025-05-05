import json
import streamlit as st
from services.dataset_service import DatasetService
from utils.preview import preview_dataset

# 页面标题
st.title("多模态数据管理平台")
st.header("预览数据集")

if st.button("刷新"):
    DatasetService.clear_cache()
    st.success("数据集列表已刷新！")
    st.rerun()

# 获取数据集列表
datasets = DatasetService.get_dataset_names()
if not datasets:
    st.info("当前尚无数据集，请先导入数据集。")
else:
    # 构建选择框选项
    options = {f"{name} (ID: {id})": id for id, name in datasets}
    
    # 如果是从列表页跳转来的，自动选中对应数据集
    default_index = 0
    if "preview_dataset_id" in st.session_state:
        for i, (id, name) in enumerate(datasets):
            if id == st.session_state["preview_dataset_id"]:
                default_index = i
                break
    
    # 数据集选择框
    selected = st.selectbox(
        "选择要预览的数据集：",
        options.keys(),
        index=default_index
    )
    
    if selected:
        dataset_id = options[selected]
        if "page_preview" not in st.session_state:
            st.session_state["page_preview"] = 0

        def update_page():
            st.session_state["page_preview"] = st.session_state.goto_page_input - 1

        cols = st.columns([1, 3])
        with cols[0]:
            goto_page = st.number_input(
                "页码",
                min_value=1,
                value=st.session_state["page_preview"] + 1,
                step=1,
                help="输入想要跳转的页码",
                key="goto_page_input",
                on_change=update_page
            )
        
        cur_page = st.session_state["page_preview"]
        new_page = preview_dataset(dataset_id, cur_page)
        
        if new_page != cur_page:
            st.session_state["page_preview"] = new_page
            st.rerun()
