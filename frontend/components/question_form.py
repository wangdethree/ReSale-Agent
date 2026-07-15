from __future__ import annotations

from typing import Any

import streamlit as st


LIST_FIELDS = {"accessories", "additional_defects"}
NUMBER_FIELDS = {"original_price"}


def render_question_form(question: dict[str, Any]) -> tuple[str | None, Any, bool]:
    st.subheader("补充商品信息")
    if question.get("completed"):
        st.success("信息已补充完整，可以生成出售方案。")
        return None, None, False

    field = question["field"]
    st.write(question["question"])
    with st.form(f"question_{field}"):
        if field in NUMBER_FIELDS:
            answer = st.number_input("答案", min_value=0.0, step=1.0)
        elif field in LIST_FIELDS:
            text = st.text_area("答案", placeholder="每行一项，例如：原包装、数据线、说明书")
            answer = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            answer = st.text_input("答案")
        submitted = st.form_submit_button("提交答案")
    return field, answer, submitted

