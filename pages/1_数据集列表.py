import json
import streamlit as st
import pandas as pd
from services.dataset_service import DatasetService
from services.group_service import GroupService

# 页面标题
st.title("多模态数据管理平台")
st.header("所有数据集")

# 添加刷新按钮
if st.button("刷新"):
    DatasetService.clear_cache()
    st.success("数据集列表已刷新！")
    st.rerun()

# 获取所有数据集
datasets = DatasetService.get_all_datasets()
if not datasets:
    st.info("当前尚无数据集")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("前往导入数据集页面"):
            st.switch_page("../pages/2_导入数据集.py")
else:
    # 添加标签筛选功能
    all_unique_tags = DatasetService.get_all_unique_tags()
    if all_unique_tags:
        st.write("按标签筛选:")
        col1, _ = st.columns([1, 3])
        with col1:
            selected_tags = st.multiselect(
                "选择标签进行筛选",
                options=all_unique_tags,
                label_visibility="collapsed"
            )
        
        # 根据标签筛选数据集
        if selected_tags:
            filtered_datasets = []
            for ds in datasets:
                ds_tags = json.loads(ds[4])  # tags_json 在索引 4
                if any(tag in ds_tags for tag in selected_tags):
                    filtered_datasets.append(ds)
            datasets = filtered_datasets
            st.write(f"已筛选: 显示包含 {', '.join(['#'+tag for tag in selected_tags])} 的 {len(datasets)} 个数据集")

    # 创建DataFrame用于显示数据集
    df_data = []
    for ds in datasets:
        ds_id, name, path, upload_time, tags_json, data_type, root_path, item_count, text_count, single_image_count, multi_image_count, video_count = ds
        tags = json.loads(tags_json)
        formatted_tags = ", ".join([f"#{t}" for t in tags]) if tags else "无"
        
        # 为每个数据集创建一行数据
        df_data.append({
            "数据集ID": ds_id,
            "数据集名称": name,
            "数据类型": data_type,
            "数据量": f"{item_count} 条",
            "纯文本": f"{text_count} 条",
            "单图": f"{single_image_count} 条",
            "多图": f"{multi_image_count} 条",
            "视频": f"{video_count} 条",
            "上传时间": upload_time.split()[0],
            "标签": formatted_tags
        })
    
    # 创建DataFrame对象
    df = pd.DataFrame(df_data)
    
    # 初始化session_state以存储选择状态
    if "selected_dataset_ids" not in st.session_state:
        st.session_state["selected_dataset_ids"] = []

    if "create_group_clicked" not in st.session_state:
        st.session_state["create_group_clicked"] = False
    
    
    # 使用st.dataframe显示数据集列表
    selection = st.dataframe(
        df,
        column_config={
            "数据集ID": None,  # 隐藏ID列
            "数据集名称": st.column_config.TextColumn("数据集名称", width="medium"),
            "数据类型": st.column_config.TextColumn("数据类型", width="small"),
            "数据量": st.column_config.TextColumn("数据量", width="small"),
            "纯文本": st.column_config.TextColumn("纯文本", width="small"),
            "单图": st.column_config.TextColumn("单图", width="small"),
            "多图": st.column_config.TextColumn("多图", width="small"),
            "视频": st.column_config.TextColumn("视频", width="small"),
            "上传时间": st.column_config.TextColumn("上传时间", width="small"),
            "标签": st.column_config.TextColumn("标签", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        selection_mode="multi-row",
        on_select="rerun",
        key="dataset_table"
    )

    # 检查是否有选择，并获取选中的数据集ID
    if "dataset_table" in st.session_state:
        selected_data = st.session_state["dataset_table"]["selection"]
        if selected_data and "rows" in selected_data and selected_data["rows"]:
            # 获取所有选中行的索引
            selected_indices = selected_data["rows"]
            # 获取所有选中的数据集ID
            selected_dataset_ids = [df.iloc[idx]["数据集ID"].item() for idx in selected_indices]
            st.session_state["selected_dataset_ids"] = selected_dataset_ids
        else:
            st.session_state["selected_dataset_ids"] = []
    else:
        st.session_state["selected_dataset_ids"] = []

    # 显示操作按钮（编辑、预览、创建分组、管理分组）
    col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 2])
    with col1:
        if st.button("编辑所选数据集", key="edit_selected"):
            st.session_state["edit_button_clicked"] = True
            st.rerun()
    
    with col2:
        if st.button("预览所选数据集", key="preview_selected"):
            st.session_state["preview_button_clicked"] = True
            st.rerun()
    
    with col3:
        if st.button("创建分组", key="create_group"):
            st.session_state["create_group_clicked"] = True
    
    with col4:
        if st.button("管理分组", key="manage_groups"):
            st.switch_page("../pages/5_分组管理.py")

    # 处理编辑按钮点击
    if st.session_state.get("edit_button_clicked", False):
        st.session_state.pop("edit_button_clicked", None)
        
        if len(st.session_state["selected_dataset_ids"]) > 1:
            st.warning("编辑功能仅支持选择单个数据集，请只选择一个数据集进行编辑")
        elif len(st.session_state["selected_dataset_ids"]) == 1:
            st.session_state["edit_dataset_id"] = st.session_state["selected_dataset_ids"][0]
            st.switch_page("../pages/4_编辑数据集.py")
        else:
            st.warning("请先选择一个数据集")

    # 处理预览按钮点击
    if st.session_state.get("preview_button_clicked", False):
        st.session_state.pop("preview_button_clicked", None)
        
        if len(st.session_state["selected_dataset_ids"]) > 0:
            if len(st.session_state["selected_dataset_ids"]) > 1:
                st.info(f"已选择{len(st.session_state['selected_dataset_ids'])}个数据集，将预览第一个选中的数据集")
            st.session_state["preview_dataset_id"] = st.session_state["selected_dataset_ids"][0]
            st.switch_page("../pages/3_预览数据集.py")
        else:
            st.warning("请先选择一个数据集")
    
    # 处理创建分组按钮点击
    if st.session_state.get("create_group_clicked", False):
        
        with st.form(key="create_group_form"):
            st.subheader("创建新分组")
            group_name = st.text_input("分组名称", placeholder="请输入分组名称")
            selected_count = len(st.session_state["selected_dataset_ids"])
            st.write(f"已选择 {selected_count} 个数据集")

            submit_button = st.form_submit_button("创建分组")
            if submit_button:
                if group_name.strip():
                    selected_ids = st.session_state["selected_dataset_ids"]
                    try:
                        ok, msg = GroupService.create_dataset_group(group_name, selected_ids)
                        if ok:
                            st.success(f"分组 '{group_name}' 创建成功: {msg}")
                            st.session_state["selected_dataset_ids"] = []
                            st.session_state["create_group_clicked"] = False  # 提交成功才关闭表单
                            st.rerun()
                        else:
                            st.error(f"创建失败: {msg}")
                    except Exception as e:
                        st.error(f"发生错误: {str(e)}")
                else:
                    st.error("分组名称不能为空")
