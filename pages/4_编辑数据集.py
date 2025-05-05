import json
import streamlit as st
from services.dataset_service import DatasetService

# 页面标题
st.title("多模态数据管理平台")
st.header("编辑数据集")

# 获取数据集列表
datasets = DatasetService.get_dataset_names()
if not datasets:
    st.info("当前尚无数据集，请先导入数据集。")
else:
    # 构建选择框选项
    options = {f"{name} (ID: {id})": id for id, name in datasets}
    
    # 如果是从列表页跳转来的，自动选中对应数据集
    default_index = 0
    if "edit_dataset_id" in st.session_state:
        for i, (id, name) in enumerate(datasets):
            if id == st.session_state["edit_dataset_id"]:
                default_index = i
                break
    
    # 数据集选择框
    selected = st.selectbox(
        "选择要编辑的数据集：",
        options.keys(),
        index=default_index
    )
    
    if selected:
        dataset_id = options[selected]
        
        # 获取数据集详细信息
        dataset = DatasetService.get_dataset_details(dataset_id)
        
        if not dataset:
            st.error("未找到对应的数据集")
        else:
            ds_id, name, path, tags_json, root_path = dataset
            tags = json.loads(tags_json)
            
            st.subheader(f"编辑数据集: {name}")
            
            # 初始化会话状态中的当前标签
            if "current_tags" not in st.session_state or st.session_state.get("last_edited_id") != ds_id:
                st.session_state["current_tags"] = tags.copy()
                st.session_state["last_edited_id"] = ds_id
            
            # 标签管理部分 - 移到表单外部
            st.subheader("管理标签")
            
            # 显示当前标签
            st.write("当前标签:")
            current_tags = st.session_state["current_tags"]
            
            # 使用列布局展示标签
            if current_tags:
                cols = st.columns(3)
                for i, tag in enumerate(current_tags):
                    col_idx = i % 3
                    with cols[col_idx]:
                        if st.button(f"❌ {tag}", key=f"remove_{ds_id}_{tag}"):
                            current_tags.remove(tag)
                            st.session_state["current_tags"] = current_tags
                            st.rerun()
            else:
                st.info("暂无标签")
            
            # 表单用于编辑数据集信息
            with st.form(f"edit_dataset_form_{ds_id}"):
                # 数据集路径编辑
                new_path = st.text_input("数据文件路径", value=path)
                
                # 根路径编辑
                new_root_path = st.text_input("根目录路径", value=root_path)
                
                # 所有可用标签
                all_tags = DatasetService.get_all_unique_tags()
                available_tags = [tag for tag in all_tags if tag not in current_tags]
                
                st.write("添加标签")
                # 添加标签区域
                col1, col2 = st.columns(2)
                
                # 从已有标签中选择
                with col1:
                    st.write("从已有标签中选择：")
                    if available_tags:
                        selected_tag = st.selectbox(
                            "选择已有标签", 
                            options=[""] + available_tags,
                            index=0,
                            key=f"select_existing_tag_{ds_id}"
                        )
                    else:
                        st.info("没有可供选择的额外标签")
                        selected_tag = ""
                
                # 添加新标签
                with col2:
                    st.write("或创建新标签：")
                    new_tag = st.text_input("新标签名称:", 
                                           placeholder="输入新标签名称",
                                           key=f"new_tag_input_{ds_id}")
                
                # 提交按钮，组合成一行
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    add_existing = st.form_submit_button("添加已有标签")
                
                with col2:
                    add_new = st.form_submit_button("创建并添加新标签")
                    
                with col3:
                    save_all = st.form_submit_button("保存所有更改")

            # 处理表单提交的操作
            if add_existing and selected_tag:
                if selected_tag not in current_tags:
                    current_tags.append(selected_tag)
                    st.session_state["current_tags"] = current_tags
                    st.rerun()
            
            if add_new and new_tag:
                if new_tag not in current_tags:
                    current_tags.append(new_tag)
                    st.session_state["current_tags"] = current_tags
                    st.rerun()
            
            if save_all:
                # 更新数据集信息
                DatasetService.update_dataset(
                    ds_id,
                    path=new_path,
                    root_path=new_root_path,
                    tags=current_tags
                )
                
                st.success("数据集信息已更新")
                st.session_state.pop("current_tags", None)
            
            # 返回按钮
            if st.button("返回数据集列表", key=f"return_button_{ds_id}"):
                st.session_state.pop("edit_dataset_id", None)
                st.session_state.pop("current_tags", None)
                st.switch_page("../pages/1_数据集列表.py")
