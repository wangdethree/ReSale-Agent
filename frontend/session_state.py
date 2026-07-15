from __future__ import annotations

import streamlit as st


DEFAULTS = {
    "session_id": None,
    "category": "digital",
    "state": {},
    "analysis": None,
    "listing": None,
    "negotiation": None,
    "current_view": "开始出售",
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_flow() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

