"""
Aplicação Principal do Streamlit: Análise Avançada de xG no Futebol Brasileiro (Estudo de Caso: Palmeiras).
Estrutura Unificada em 3 Visões Executivas:
1. 📊 Raio-X & Panorama Geral (Identidade, Linha do Tempo, Shotmap e Fases)
2. ⚔️ O que Mudou? (Comparador Tático & Diagnóstico Causal de Rendimento)
3. 🛡️ O Modelo de Abel: Formações Táticas & Prancheta Interativa
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from app.modules.view1_overview import render_overview_view
from app.modules.view2_comparison import render_comparison_view
from app.modules.view3_tactics import render_tactics_view

st.set_page_config(
    page_title="Análise Avançada de xG | Palmeiras",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS para refinamento visual
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #00FF87;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 1.02rem;
        color: #9bb0cf;
        margin-bottom: 22px;
    }
    .badge-card {
        background-color: #1a2234;
        border: 1px solid #2d3a56;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 15px;
    }
    div[data-testid="stSidebar"] {
        background-color: #0f1420;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #161f30;
        border-radius: 6px 6px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #cbd5e1;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #00FF87 !important;
        border-bottom: 3px solid #00FF87 !important;
    }
</style>
""", unsafe_allow_html=True)

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

@st.cache_data
def _load_data_cached(mtime_matches: float, mtime_shots: float):
    matches_file = PROCESSED_DIR / "matches.parquet"
    shots_file = PROCESSED_DIR / "shots.parquet"
    df_matches = pd.read_parquet(matches_file)
    df_shots = pd.read_parquet(shots_file)
    return df_matches, df_shots

def load_data():
    matches_file = PROCESSED_DIR / "matches.parquet"
    shots_file = PROCESSED_DIR / "shots.parquet"

    if not matches_file.exists() or not shots_file.exists():
        return None, None

    mtime_m = matches_file.stat().st_mtime
    mtime_s = shots_file.stat().st_mtime

    df_matches, df_shots = _load_data_cached(mtime_m, mtime_s)

    # Verificação de integridade: se o cache em memória for antigo e não tiver as novas colunas
    if "palmeiras_formation" not in df_matches.columns or "field_tilt" not in df_matches.columns:
        st.cache_data.clear()
        df_matches = pd.read_parquet(matches_file)
        df_shots = pd.read_parquet(shots_file)

    return df_matches, df_shots

def main():
    st.markdown('<div class="main-title">⚽ Análise Avançada de xG: Estudo de Caso Palmeiras</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Inteligência tática, decomposição causal e diagnóstico profundo do rendimento do Palmeiras de Abel Ferreira.</div>', unsafe_allow_html=True)

    df_matches, df_shots = load_data()

    if df_matches is None or df_shots is None:
        st.error("Arquivos de dados não encontrados em `data/processed/`. Por favor, execute o pipeline de dados primeiro.")
        return

    # --- SIDEBAR (Filtros para a Visão 1: Panorama) ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg", width=85)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("🔄 Recarregar", on_click=st.cache_data.clear, use_container_width=True, help="Limpa o cache em memória")
        with col_btn2:
            if st.button("⚡ Sincronizar", use_container_width=True, help="Verifica a API do SofaScore e baixa novos jogos finalizados automaticamente"):
                with st.spinner("Buscando novos jogos no SofaScore..."):
                    from src.ingestion.sync_recent import sync_new_matches
                    n_new, descs = sync_new_matches()
                    if n_new > 0:
                        st.cache_data.clear()
                        st.success(f"🎉 {n_new} novo(s) jogo(s) adicionado(s)!\n" + "\n".join([f"• {d}" for d in descs]))
                        st.rerun()
                    else:
                        st.info("✅ Todos os jogos já estão 100% atualizados!")
        st.markdown("---")
        st.markdown("### 🔍 Filtros do Panorama")
        st.caption("Filtros aplicados à aba **1. Raio-X & Panorama**. As abas **2** e **3** contêm seletores comparativos dedicados.")

        # Atalhos rápidos (Presets)
        st.markdown("**Atalhos Rápidos:**")
        col_p1, col_p2 = st.columns(2)
        p_all = col_p1.button("🌐 Todas", use_container_width=True)
        p_2026 = col_p2.button("📅 2026", use_container_width=True)
        col_p3, col_p4 = st.columns(2)
        p_bra = col_p3.button("🏆 Brasileirão", use_container_width=True)
        p_lib = col_p4.button("⭐ Libertadores", use_container_width=True)

        available_seasons = sorted(list(df_matches["season"].dropna().unique()), reverse=True)
        available_tournaments = sorted(list(df_matches["tournament"].dropna().unique()))

        if "sel_seasons" not in st.session_state:
            st.session_state.sel_seasons = [available_seasons[0]] if available_seasons else []
        if "sel_tournaments" not in st.session_state:
            st.session_state.sel_tournaments = available_tournaments

        if p_all:
            st.session_state.sel_seasons = available_seasons
            st.session_state.sel_tournaments = available_tournaments
        elif p_2026:
            st.session_state.sel_seasons = ["2026"]
        elif p_bra:
            st.session_state.sel_tournaments = [t for t in available_tournaments if "brasileir" in t.lower()]
        elif p_lib:
            st.session_state.sel_tournaments = [t for t in available_tournaments if "libertadores" in t.lower()]

        # 1. Filtro de Temporadas
        selected_seasons = st.multiselect(
            "Temporada(s):",
            available_seasons,
            default=st.session_state.sel_seasons
        )

        # 2. Filtro de Competições
        selected_tournaments = st.multiselect(
            "Competição(ões):",
            available_tournaments,
            default=st.session_state.sel_tournaments
        )

        # 3. Mando de Campo
        mando_choice = st.radio("Mando de Campo:", ["Todos", "Apenas Mandante", "Apenas Visitante"], horizontal=True)

        # 4. Toggle xG
        only_with_xg = st.checkbox("Filtrar apenas jogos com xG", value=True)

        st.markdown("---")

        # Indicador de Cobertura Amostral
        raw_filtered_matches = df_matches[
            (df_matches["season"].isin(selected_seasons)) &
            (df_matches["tournament"].isin(selected_tournaments))
        ]
        if mando_choice == "Apenas Mandante":
            raw_filtered_matches = raw_filtered_matches[raw_filtered_matches["is_palmeiras_home"] == True]
        elif mando_choice == "Apenas Visitante":
            raw_filtered_matches = raw_filtered_matches[raw_filtered_matches["is_palmeiras_home"] == False]

        total_sample = len(raw_filtered_matches)
        total_xg_sample = (raw_filtered_matches["has_xg"] == True).sum()
        pct_cov = (total_xg_sample / total_sample * 100) if total_sample > 0 else 0
        total_adv_sample = (raw_filtered_matches["has_advanced_stats"] == True).sum() if "has_advanced_stats" in raw_filtered_matches else 0
        pct_adv = (total_adv_sample / total_sample * 100) if total_sample > 0 else 0

        st.markdown(f"""
        <div class="badge-card">
            <span style="color:#00FF87; font-weight:bold;">📡 Cobertura da Amostra (Panorama):</span><br>
            • Partidas Filtradas: <b>{total_sample}</b><br>
            • Com Shotmap e xG: <b>{total_xg_sample}</b> ({pct_cov:.0f}%)<br>
            • Com Métricas Táticas (Field Tilt): <b>{total_adv_sample}</b> ({pct_adv:.0f}%)
        </div>
        """, unsafe_allow_html=True)
        st.caption("Base: SofaScore API | Palmeiras xG Analytics")

    # Aplicar filtros da sidebar aos DataFrames para a Visão 1
    filtered_matches = raw_filtered_matches.copy()
    if only_with_xg:
        filtered_matches = filtered_matches[filtered_matches["has_xg"] == True]

    match_ids = filtered_matches["match_id"].unique()
    filtered_shots = df_shots[df_shots["match_id"].isin(match_ids)].copy()

    # --- 3 ABAS PRINCIPAIS UNIFICADAS ---
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Raio-X & Panorama Geral",
        "⚔️ 2. O que Mudou? (Comparador & Diagnóstico Causal)",
        "🛡️ 3. O Modelo de Abel: Formações & Campo"
    ])

    with tab1:
        render_overview_view(filtered_shots, filtered_matches)

    with tab2:
        render_comparison_view(df_shots, df_matches)

    with tab3:
        render_tactics_view(df_matches)

if __name__ == "__main__":
    main()
