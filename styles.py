import streamlit as st


THEMES = {
    "Default": {
        "bg": "#eef4ff",
        "panel": "#eef4ff",
        "panel_alt": "#dde7ff",
        "text": "#172033",
        "muted": "#667085",
        "border": "#cdd9ee",
        "accent": "#2563eb",
        "accent_soft": "#dbe5ff",
        "accent_two": "#f59e0b",
        "input": "#ffffff",
        "shadow": "0 12px 28px rgba(18, 31, 50, .06)",
    },
    "Light": {
        "bg": "#f6fbfb",
        "panel": "#f5f8ff",
        "panel_alt": "#e8f1ff",
        "text": "#111827",
        "muted": "#5f6f68",
        "border": "#d1dde9",
        "accent": "#0f766e",
        "accent_soft": "#e6f5f2",
        "accent_two": "#2563eb",
        "input": "#ffffff",
        "shadow": "0 10px 24px rgba(17, 24, 39, .05)",
    },
    "Dark": {
        "bg": "#0c1220",
        "panel": "#141c2b",
        "panel_alt": "#1b2637",
        "text": "#f8fafc",
        "muted": "#c3cede",
        "border": "#334155",
        "accent": "#38bdf8",
        "accent_soft": "#123348",
        "accent_two": "#fbbf24",
        "input": "#111827",
        "shadow": "0 12px 30px rgba(0, 0, 0, .22)",
    },
}

def apply_theme(mode: str = "Default") -> None:
    palette = THEMES.get(mode, THEMES["Default"])
    st.markdown(
        f"""
        <style>
        .stApp,
        .stApp > header,
        [data-testid="stAppViewContainer"] {{
            background: {palette["bg"]} !important;
            color: {palette["text"]} !important;
        }}
        .block-container {{
            padding-top: 1.5rem;
            max-width: 1280px;
        }}
        .block-container::before {{
            content: "";
            display: block;
            height: 4px;
            width: 100%;
            margin-bottom: 1rem;
            border-radius: 999px;
            background: linear-gradient(90deg, {palette["accent"]}, {palette["accent_two"]});
        }}
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {{
            background: {palette["panel"]} !important;
            color: {palette["text"]} !important;
        }}
        [data-testid="stSidebar"] {{
            border-right: 1px solid {palette["border"]};
        }}
        h1, h2, h3, h4, h5, h6, p, label, span, div {{
            letter-spacing: 0;
        }}
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"],
        [data-testid="stText"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {{
            color: {palette["text"]} !important;
        }}
        small, .stCaptionContainer,
        [data-testid="stCaptionContainer"],
        [data-testid="stMetricDelta"] {{
            color: {palette["muted"]} !important;
        }}
        .auth-shell {{
            max-width: 980px;
            margin: 0 auto;
            padding: 1.5rem 0 0;
        }}
        .auth-header {{
            background: {palette["panel"]};
            border: 1px solid {palette["border"]};
            border-radius: 8px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: {palette["shadow"]};
            border-top: 4px solid {palette["accent"]};
        }}
        .auth-header h1 {{
            font-size: 2rem;
            margin: 0 0 .35rem 0;
            color: {palette["text"]};
        }}
        .auth-header p {{
            color: {palette["muted"]};
            margin: 0;
        }}
        .google-badge {{
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            font-weight: 700;
            color: {palette["text"]};
            margin-top: .35rem;
        }}
        .google-mark {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-grid;
            place-items: center;
            font-weight: 800;
            color: #4285f4;
            background: #ffffff;
            border: 1px solid #cfd8e3;
        }}
        div[data-testid="stMetric"],
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stDataFrame"],
        .stDataFrame,
        .stAlert {{
            background: {palette["panel"]} !important;
            border: 1px solid {palette["border"]} !important;
            border-radius: 8px !important;
            color: {palette["text"]} !important;
        }}
        div[data-testid="stMetric"] {{
            padding: .9rem 1rem;
            box-shadow: {palette["shadow"]};
            border-top: 3px solid {palette["accent"]} !important;
        }}
        .theme-status {{
            text-align: right;
            color: {palette["muted"]};
            font-size: .85rem;
            margin-top: -.35rem;
            margin-bottom: .35rem;
        }}
        input, textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="base-input"] input,
        [data-baseweb="textarea"] textarea {{
            background: {palette["input"]} !important;
            color: {palette["text"]} !important;
            border-color: {palette["border"]} !important;
        }}
        [data-baseweb="popover"] > div,
        [role="listbox"] {{
            background: {palette["panel"]} !important;
            color: {palette["text"]} !important;
            border: 1px solid {palette["border"]} !important;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: .25rem;
            border-bottom-color: {palette["border"]} !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            background: {palette["panel"]};
            border: 1px solid {palette["border"]};
            border-radius: 8px 8px 0 0;
            padding: .6rem 1rem;
            color: {palette["text"]};
        }}
        .stTabs [aria-selected="true"] {{
            color: {palette["accent"]} !important;
            border-bottom: 3px solid {palette["accent"]} !important;
        }}
        .stApp form button,
        .stApp form button *,
        .stApp a[data-testid="stLinkButton"],
        .stApp a[data-testid="stLinkButton"] *,
        .stApp [data-testid="stLinkButton"] button,
        .stApp [data-testid="stLinkButton"] button * {{
            background-color: {palette["accent"]} !important;
            color: #ffffff !important;
            border-color: {palette["accent"]} !important;
            background-image: none !important;
            box-shadow: none !important;
        }}
        .stApp form button {{
            border-radius: 8px !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: {palette["panel_alt"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
