from __future__ import annotations

import streamlit as st


CATEGORY_OPTIONS = {
    "digital": "数码产品",
    "book": "图书",
    "appliance": "小家电",
    "clothing": "服装",
}


def render_upload_panel() -> tuple[str, list[object]]:
    st.subheader("开始出售")
    st.caption("上传 1～4 张 JPG/PNG 图片，系统会先给出可编辑的识别初稿。")
    category = st.selectbox(
        "商品类别",
        options=list(CATEGORY_OPTIONS.keys()),
        format_func=lambda value: CATEGORY_OPTIONS[value],
    )
    files = st.file_uploader(
        "商品图片",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="单张建议不超过 10 MB。",
    )
    if files:
        cols = st.columns(min(len(files), 4))
        for index, file in enumerate(files[:4]):
            with cols[index % len(cols)]:
                st.image(file, use_container_width=True)
    return category, list(files or [])
