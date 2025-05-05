import json
import streamlit as st
import pandas as pd
from services.group_service import GroupService
from services.dataset_service import DatasetService
from utils.database import get_db_connection
from utils.group import clear_groups_cache

# 页面标题
st.title("多模态数据管理平台")
st.header("数据集分组管理")

# 获取所有分组
groups = GroupService.get_all_groups()

if not groups:
    st.info("当前尚无数据集分组，请先在数据集列表页创建分组。")
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("返回数据集列表"):
            st.switch_page("../pages/1_数据集列表.py")
else:
    # 添加刷新按钮
    if st.button("刷新"):
        GroupService.clear_groups_cache()
        st.success("分组列表已刷新！")
        st.rerun()
    
    # 创建DataFrame用于显示分组
    df_data = []
    for group in groups:
        group_id, name, dataset_ids_json, create_time = group
        dataset_ids = json.loads(dataset_ids_json)
        
        # 为每个分组创建一行数据
        df_data.append({
            "分组ID": group_id,
            "分组名称": name,
            "数据集数量": len(dataset_ids),
            "创建时间": create_time.split()[0],
        })
    
    # 创建DataFrame对象
    df = pd.DataFrame(df_data)
    
    # 使用st.dataframe显示分组列表
    st.dataframe(
        df,
        column_config={
            "分组ID": st.column_config.TextColumn("分组ID", width="small"),
            "分组名称": st.column_config.TextColumn("分组名称", width="medium"),
            "数据集数量": st.column_config.TextColumn("数据集数量", width="small"),
            "创建时间": st.column_config.TextColumn("创建时间", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 显示分组详情和操作
    st.subheader("分组操作")
    
    # 选择分组
    group_options = {f"{name} (ID: {id})": id for id, name, _, _ in groups}
    selected_group = st.selectbox("选择分组", options=list(group_options.keys()))
    
    if selected_group:
        group_id = group_options[selected_group]
        
        # 获取分组详情
        group_details = GroupService.get_group_details(group_id)
        
        if group_details:
            # 获取数据集映射 id->name
            dataset_names = {id: name for id, name in DatasetService.get_dataset_names()}
            
            # 显示分组包含的数据集
            st.subheader(f"分组 '{group_details['name']}' 包含的数据集")
            
            dataset_list = []
            for ds_id in group_details["dataset_ids"]:
                if ds_id in dataset_names:
                    dataset_list.append(dataset_names[ds_id])
            
            # 统计面板
            st.subheader("📊 数据统计")
            
            # 从服务层获取统计信息
            stats = GroupService.get_group_stats(group_id)
            total_items = stats['total']
            type_dist = {
                "text": stats['text'],
                "image": stats['single_image'],
                "multi-image": stats['multi_image'],
                "video": stats['video']
            }
            dataset_dist = stats['datasets']
            
            # 显示核心指标
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总数据量", f"{total_items:,} 条")
            with col2:
                st.metric("数据类型", f"{len(type_dist)} 类")
            with col3:
                st.metric("包含数据集", f"{len(dataset_dist)} 个")
            
            # 类型分布图表
            st.subheader("📊 数据类型分布")
            import plotly.express as px
            fig = px.pie(
                names=["文本", "单图", "多图", "视频"],
                values=[
                    type_dist["text"],
                    type_dist["image"],
                    type_dist["multi-image"],
                    type_dist["video"]
                ],
                title="数据类型占比",
                hole=0.3,
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 数据集占比
            st.subheader("📦 数据集占比")
            if total_items > 0:
                dataset_percent = {k: v/total_items*100 for k,v in dataset_dist.items()}
                st.write("各数据集数据量占比：")
                for name, pct in dataset_percent.items():
                    st.progress(pct/100, text=f"{name} ({pct:.1f}%)")
            else:
                st.info("该分组暂无数据")
            
            # 操作按钮
            st.subheader("⚙️ 分组操作")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("导出分组信息", key=f"export_{group_id}"):
                    export_data = GroupService.export_group_info(group_id)
                    if export_data:
                        st.subheader("导出信息")
                        # st.json(export_data)
                        # 提供复制按钮
                        st.code(json.dumps(export_data, indent=2, ensure_ascii=False))
                    else:
                        st.error("导出分组信息失败")
            
            with col2:
                if st.button("删除分组", key=f"delete_{group_id}"):
                    # 使用session_state来跟踪确认状态
                    confirm_key = f"confirm_delete_{group_id}"
                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False
                    
                    if st.session_state[confirm_key]:
                        ok, msg = GroupService.delete_dataset_group(group_id)
                        if ok:
                            st.success(msg)
                            # 清除确认状态并刷新页面
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.session_state[confirm_key] = True
                        st.warning(f"确定要删除分组 '{group_details['name']}' 吗？再次点击'删除分组'按钮确认")
