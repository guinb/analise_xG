"""
Script mestre de execução completa do pipeline de dados:
1. Executa a ingestão (descoberta + download com cache de shotmaps e incidentes).
2. Executa o processamento (engenharia de features, geometria FIFA e motor de Game State).
3. Salva os arquivos normalizados em Parquet e imprime estatísticas finais.
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ingestion.sofascore_client import SofaScoreClient
from src.ingestion.fetch_data import discover_all_matches, filter_matches, fetch_events_data
from src.processing.pipeline import run_processing_pipeline

def main():
    parser = argparse.ArgumentParser(description="Pipeline Completo de Análise de xG")
    parser.add_argument("--seasons", nargs="+", default=["2023", "2024", "2025", "2026"], help="Temporadas a processar")
    parser.add_argument("--pages", type=int, default=8, help="Páginas de histórico da equipe")
    args = parser.parse_args()

    print("==================================================================")
    print("🚀 INICIANDO PIPELINE DE DADOS: ANÁLISE AVANÇADA DE xG (PALMEIRAS)")
    print(f"Temporadas: {args.seasons} | Páginas: {args.pages}")
    print("==================================================================")

    # 1. Ingestão
    print("\n[Etapa 1/2] Ingestão de Dados via SofaScore API...")
    client = SofaScoreClient(delay_seconds=0.6)
    all_events = discover_all_matches(client, max_pages=args.pages)
    target_matches = filter_matches(all_events, target_seasons=args.seasons)
    print(f"Partidas identificadas para as temporadas selecionadas: {len(target_matches)}")
    ingest_stats = fetch_events_data(client, target_matches)

    # 2. Processamento
    print("\n[Etapa 2/2] Processamento, Geometria Espacial e Game State...")
    processed_dfs = run_processing_pipeline(seasons=args.seasons)
    df_matches = processed_dfs["matches"]
    df_shots = processed_dfs["shots"]

    print("\n==================================================================")
    print("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"Total de Partidas Processadas: {len(df_matches)}")
    print(f"Partidas com Shotmap e xG: {(df_matches['has_xg'] == True).sum()}")
    print(f"Total de Finalizações Registradas: {len(df_shots)}")
    print(f"Finalizações do Palmeiras: {(df_shots['is_palmeiras'] == True).sum()}")
    print(f"Gols Marcados pelo Palmeiras: {df_shots[df_shots['is_palmeiras'] == True]['is_goal'].sum()}")
    print(f"xG Acumulado do Palmeiras: {df_shots[df_shots['is_palmeiras'] == True]['xg'].sum():.2f}")
    print("Arquivos salvos em: data/processed/matches.parquet e data/processed/shots.parquet")
    print("Para iniciar o dashboard, execute: .venv\\Scripts\\streamlit run app/streamlit_app.py")
    print("==================================================================")

if __name__ == "__main__":
    main()
