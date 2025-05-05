import streamlit as st
from app.navigation import setup_navigation

def main():
    st.set_page_config(page_title="多模态数据管理平台", layout="wide")
    setup_navigation()

if __name__ == "__main__":
    main()
