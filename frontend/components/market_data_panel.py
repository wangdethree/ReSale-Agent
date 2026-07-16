from __future__ import annotations

from typing import Any

import streamlit as st


def render_market_data_import() -> dict[str, Any] | None:
    with st.expander("价格数据源", expanded=False):
        source_name = st.text_input("来源名称", value="个人整理样本", key="market-data-source-name")
        uploaded = st.file_uploader("成交样本 CSV", type=["csv"], key="market-data-csv")
        st.caption("必填列：category、product_type、sold_price")
        if st.button("导入样本", disabled=uploaded is None):
            return {"file": uploaded, "source_name": source_name}
    return None


def render_market_data_import_result(result: dict[str, Any]) -> None:
    st.success(
        f"导入 {result.get('imported_count', 0)} 条，"
        f"跳过 {result.get('skipped_count', 0)} 条，"
        f"错误 {result.get('error_count', 0)} 条。"
    )
    errors = result.get("errors", [])
    if errors:
        with st.expander("错误行", expanded=False):
            for error in errors:
                st.write(f"- 第 {error.get('row_number')} 行：{error.get('message')}")
