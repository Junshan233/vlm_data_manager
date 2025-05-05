import json
import streamlit as st
from services.dataset_service import DatasetService
from services.group_service import GroupService

# 页面标题
st.title("多模态数据管理平台")
st.header("导入新数据集")

# 显示上一次的导入结果
if 'import_status' in st.session_state and 'import_message' in st.session_state:
    if st.session_state.import_status:
        st.success(st.session_state.import_message)
        if st.button("刷新页面"):
            del st.session_state.import_status
            del st.session_state.import_message
            st.rerun()
    else:
        st.error(st.session_state.import_message)

# 创建选项卡
tab1, tab2 = st.tabs(["单个导入", "批量导入"])

# 单个导入选项卡
with tab1:
    ds_name = st.text_input("数据集名称", help="自定义唯一名称，用于区分不同数据集")
    root_path = st.text_input("根目录路径", help="图片和视频的根目录绝对路径")
    data_path = st.text_input("JSONL 文件路径", help="符合格式要求的 .jsonl 文件绝对路径")

    if st.button("开始导入", key="single_import"):
        if not all([ds_name, root_path, data_path]):
            st.error("请填写完整的信息后再导入")
        else:
            # 添加进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def show_progress(stage, progress):
                status_text.text(f"导入进度: {stage}")
                progress_bar.progress(progress)
            
            ok, msg, _ = DatasetService.import_jsonl_dataset(ds_name, root_path, data_path, show_progress)
            st.session_state.import_status = ok
            st.session_state.import_message = msg
            st.rerun()

# 批量导入选项卡
with tab2:
    st.markdown("""
    请提供符合以下格式的 JSON 配置：
    ```json
    {
        "数据集名称1": {
            "root": "根目录路径1",
            "annotation": "JSONL文件路径1"
        },
        "数据集名称2": {
            "root": "根目录路径2",
            "annotation": "JSONL文件路径2"
        }
    }
    ```
    """)
    
    with st.form(key="batch_import_form"):
        json_config = st.text_area(
            "JSON 配置",
            height=200,
            placeholder='在此粘贴 JSON 格式的配置...'
        )
        
        # 添加创建分组选项
        create_group = st.checkbox("创建分组", value=False)
        group_name = st.text_input("分组名称",
                                 placeholder="请输入分组名称",
                                 help="为本次导入的数据集创建分组")
        
        submit_button = st.form_submit_button("开始批量导入")
        
        if submit_button:
            if not json_config:
                st.error("请提供 JSON 配置")
            else:
                try:
                    config = json.loads(json_config)
                    
                    # 验证分组名称
                    if create_group and not group_name.strip():
                        st.error("请填写分组名称")
                        st.stop()
                    
                    # 添加进度条
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def show_progress(stage, progress):
                        status_text.text(f"导入进度: {stage}")
                        progress_bar.progress(progress)
                    
                    ok, msg, imported_ids = DatasetService.batch_import_datasets(config, show_progress)
                    st.session_state.import_status = ok
                    st.session_state.import_message = msg
                    
                    # 如果导入成功且选择了创建分组
                    if ok and create_group and imported_ids:
                        try:
                            group_ok, group_msg = GroupService.create_dataset_group(
                                group_name,
                                imported_ids
                            )
                            if group_ok:
                                msg += f"\n分组 '{group_name}' 创建成功"
                            else:
                                msg += f"\n分组创建失败: {group_msg}"
                        except Exception as e:
                            msg += f"\n分组创建时发生错误: {str(e)}"
                    
                    st.session_state.import_message = msg
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("JSON 格式错误，请检查配置")
