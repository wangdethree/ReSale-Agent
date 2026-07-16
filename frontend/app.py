from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


# Streamlit 直跑 frontend/app.py 时会优先使用脚本目录，这里补上项目根目录以便加载 frontend 包。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from frontend.api_client import ApiClient
from frontend.components.confirmation_form import render_confirmation_form
from frontend.components.negotiation_panel import render_negotiation_panel, render_negotiation_result
from frontend.components.pricing_card import render_listing
from frontend.components.question_form import render_question_form
from frontend.components.upload_panel import CATEGORY_OPTIONS, render_upload_panel
from frontend.session_state import init_state, reset_flow


st.set_page_config(page_title="ReSale Agent", page_icon="R", layout="wide")
init_state()
client = ApiClient()


def _set_view(view: str) -> None:
    st.session_state.current_view = view


def _sync_state(response: dict) -> None:
    st.session_state.session_id = response.get("session_id", st.session_state.session_id)
    st.session_state.state = response.get("state", st.session_state.state)


st.title("ReSale Agent")
st.caption("AI 二手物品出售助手 · V1 Demo")

with st.sidebar:
    st.write("当前会话")
    st.code(st.session_state.session_id or "尚未创建")
    st.radio(
        "步骤",
        ["开始出售", "确认识别结果", "补充商品信息", "出售方案", "模拟议价"],
        key="current_view",
    )
    if st.button("重新开始"):
        reset_flow()
        st.rerun()


try:
    if st.session_state.current_view == "开始出售":
        category, files = render_upload_panel()
        st.session_state.category = category
        disabled = not files or len(files) > 4
        if st.button("开始识别", disabled=disabled):
            created = client.create_session(category)
            _sync_state(created)
            analysis = client.analyze_images(st.session_state.session_id, files)
            st.session_state.analysis = analysis
            _set_view("确认识别结果")
            st.rerun()

    elif st.session_state.current_view == "确认识别结果":
        if not st.session_state.analysis:
            st.info("请先在“开始出售”上传图片并开始识别。")
        else:
            product = st.session_state.analysis["product"]
            confirmed = render_confirmation_form(product, st.session_state.category)
            if confirmed:
                response = client.confirm_product(st.session_state.session_id, confirmed)
                _sync_state(response)
                _set_view("补充商品信息")
                st.rerun()

    elif st.session_state.current_view == "补充商品信息":
        if not st.session_state.session_id:
            st.info("请先创建出售会话。")
        else:
            question = client.next_question(st.session_state.session_id)
            field, answer, submitted = render_question_form(question)
            if question.get("completed"):
                if st.button("生成出售方案"):
                    st.session_state.listing = client.generate_listing(st.session_state.session_id)
                    _set_view("出售方案")
                    st.rerun()
            elif submitted and field:
                client.answer_question(st.session_state.session_id, field, answer)
                st.rerun()

    elif st.session_state.current_view == "出售方案":
        if not st.session_state.listing:
            if st.session_state.session_id and st.button("生成出售方案"):
                st.session_state.listing = client.generate_listing(st.session_state.session_id)
                st.rerun()
            else:
                st.info("信息补充完整后再生成出售方案。")
        else:
            render_listing(st.session_state.listing)
            markdown = client.export_markdown(st.session_state.session_id)
            st.download_button("下载 Markdown 报告", markdown, file_name="resale-agent-report.md")
            if st.button("进入模拟议价"):
                _set_view("模拟议价")
                st.rerun()

    elif st.session_state.current_view == "模拟议价":
        default_floor = None
        if st.session_state.listing:
            default_floor = st.session_state.listing["price"]["suggested_floor_price"]
        buyer_message, floor, submitted = render_negotiation_panel(default_floor)
        if submitted and buyer_message:
            st.session_state.negotiation = client.negotiation_reply(st.session_state.session_id, buyer_message, floor)
        if st.session_state.negotiation:
            render_negotiation_result(st.session_state.negotiation)

except RuntimeError as exc:
    st.error(str(exc))


st.divider()
st.caption(
    f"支持类别：{', '.join(CATEGORY_OPTIONS.values())}。当前版本使用本地模拟数据，不代表真实平台成交价。"
)
