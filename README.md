# Análise Avançada de xG no Futebol Brasileiro (Estudo de Caso: Palmeiras)

Projeto de Data Science e Sports Analytics focado em desmistificar e elevar a discussão tática em torno do **Expected Goals (xG)** no futebol brasileiro, utilizando o **Palmeiras** (2023–2026) como estudo de caso longitudinal em todas as competições oficiais (Brasileirão Série A, Copa Libertadores, Copa do Brasil e Campeonato Paulista).

---

## 🎯 Por que Elevar a Discussão sobre o xG?

No debate esportivo contemporâneo, a métrica de **xG** é frequentemente utilizada de forma simplista ou descontextualizada. Os principais equívocos observados no debate público incluem:

1. **O Mito do xG Agregado Isolado:** Comparar apenas o somatório de xG da partida ignora a composição das finalizações. Uma equipe que produz $2.0$ de xG com 20 chutes de $0.10$ (bombardeio de fora da área) possui uma dinâmica ofensiva totalmente diferente de outra que produz $2.0$ com 3 chances claríssimas de $0.67$.
2. **A Ignorância do Efeito do Placar (*Game State*):** Equipes que abrem o placar cedo naturalmente baixam as linhas, controlam o espaço e convidam o adversário a finalizar de longe. O adversário infla seu volume de xG no "desespero", gerando uma falsa impressão de domínio.
3. **Confusão entre Eficiência e Variância:** Atacantes em fases de seca ou sorte temporária são julgados precipitadamente. A métrica $G - xG$ (Gols Reais menos Esperados) decompõe o que é variância probabilística e o que é qualidade de finalização sustentável.
4. **Desconexão com as Fases de Jogo:** Rotular equipes como puramente reativas ou dependentes de bola parada sem mensurar o share real de criação em Jogo Aberto, Escanteios, Faltas e Contra-Ataques.

---

## 🏛️ Arquitetura da Solução

O projeto é dividido em quatro camadas modulares:

```text
analise_xg/
├── data/
│   ├── raw/                      # Cache de JSONs brutos da API (shotmaps, eventos e incidentes)
│   └── processed/                # DataFrames normalizados e limpos em Parquet
│       ├── matches.parquet       # Metadados de cada partida (placar, minutos por estado, xG)
│       └── shots.parquet         # Todos os chutes individuais com coordenadas FIFA, xG e Game State
├── src/
│   ├── ingestion/                # Cliente SofaScore com curl_cffi, rate-limiting e cache
│   ├── processing/               # Engenharia de features geométricas e motor de Game State
│   ├── analytics/                # Decomposição de xG, Simulação Monte Carlo e Métricas por Atleta
│   └── visualization/            # Shotmaps interativos (Plotly) e cards editoriais (Mplsoccer)
├── app/
│   ├── streamlit_app.py          # Dashboard interativo principal
│   └── modules/                  # Os 5 módulos analíticos do Streamlit
├── scripts/
│   ├── 00_probe_sofascore.py     # Sonda de teste de conectividade e schemas
│   ├── run_pipeline.py           # Pipeline unificado de ingestão e processamento
│   └── verify_parquet.py         # Teste automatizado de sanidade dos dados
└── requirements.txt              # Dependências do projeto
```

---

## 📊 Os 5 Módulos Analíticos no Dashboard

### 1. Decomposição: Volume vs. Qualidade
- Decompõe formalmente a geração ofensiva em:
  $$\text{xG/90} = \text{Shots/90} \times \text{xG/shot}$$
- Gráficos de dispersão interativos entre Volume e Qualidade média por competição e temporada.
- Histograma da distribuição de perigo: *Grandes Chances* ($xG \ge 0.30$), *Média*, *Baixa* e *Especulativa* ($xG < 0.04$).
- Métricas espaciais regulamentares: distância média ao gol e ângulo de visão da trave em graus.

### 2. Efeito Game State (O Mito do Placar)
- Reconstrói a linha do tempo cronológica de gols para determinar o placar exato antes de cada chute.
- Calcula os minutos passados em cada estado: **Vencendo**, **Empatando** e **Perdendo**.
- Normaliza a produção de $xG_{for}/90$ e concessão de $xG_{against}/90$ por minutos reais de cada estado.
- Shotmap interativo com filtro por estado de jogo.

### 3. Anatomia da Criação (Fases de Jogo)
- Classificação de cada finalização por situação tática:
  - *Jogo Aberto* (posse e triangulações)
  - *Bola Parada* (escanteios e faltas laterais)
  - *Contra-Ataque* (transições rápidas)
  - *Pênalti*
- Share comparativo de volume de chutes vs. xG produzido.
- Eficiência média de perigo ($xG/chute$) por mecânica de criação.

### 4. Simulação Monte Carlo & Variância Estatística
- **10.000 iterações binomiais** simulando o resultado de cada chute tomado por Palmeiras e adversário.
- Probabilidade real de Vitória, Empate e Derrota, gerando os **Pontos Esperados (xPTS)**.
- Linha do tempo acumulada de xG minuto a minuto para qualquer partida histórica da base.
- Média móvel de 5 jogos do Saldo de xG ($xGD = xG_{for} - xG_{against}$) para identificar tendências estruturais.

### 5. Raio-X por Jogador, Eficiência & Heatmap Real de Toques
- Tabela analítica completa de finalizadores: Gols, xG, $G - xG$, taxa de conversão, distância média e parte do corpo.
- Matriz de dispersão: Volume de chances acumuladas ($xG$) vs. Saldo de finalização ($G - xG$).
- Seletor individual de atletas (Estêvão, Veiga, Flaco López, etc.) com **Shotmap Interativo Plotly**, **Card Editorial Mplsoccer exportável em alta resolução (PNG)** e **Heatmap Real de Toques em Campo** (todos os toques na bola em qualquer partida histórica).

### 6. Diagnóstico Tático & O que Mudou? (Abel Ferreira 2023–2026)
- **Decomposição Fatorial Waterfall:** Separa matematicamente o $\Delta xG_{90}$ em *Efeito Volume* (chutar mais) e *Efeito Qualidade* (chutar de melhores posições):
  $$\Delta xG_{90} = \Delta V \cdot \bar{Q} + \bar{V} \cdot \Delta Q$$
- **Geometria Espacial & Corredores:** Mudança no direcionamento de ataque (Corredor Esquerdo, Central e Direito) e disciplina de finalização (dentro vs. fora da área).
- **Identidade Tática:** Evolução da fatia de xG gerada em Jogo Aberto, Bola Parada e Contra-Ataques ao longo das temporadas.
- **Formações Táticas & Domínio Territorial (Field Tilt):** Comparação estatística entre Linha de 4 (`4-2-3-1`, `4-3-3`, `4-4-2`) e Linha de 3 (`3-4-2-1`, `3-5-2`) em aproveitamento, saldo de xG, Field Tilt (% posse no terço final) e toques na área adversária.
- **Cruzamentos vs. Passes em Profundidade:** Avaliação longitudinal se a equipe se tornou mais focada em chuveirinho na área ou em bolas enfiadas por dentro.

---

## ⚔️ Modo Comparação Direta (A vs. B)

Permite contrastar dois recortes temporais ou contextuais arbitrários:
- **Temporada 2026 vs. 2025**
- **Brasileirão: 1º Turno vs. 2º Turno**
- **Competições: Brasileirão vs. Libertadores**

Inclui:
- **8 Cards com Deltas Comparativos:** xG/90, Chutes/90, xG/Chute, Gols/90, Field Tilt (%), Toques na Área/Jogo, Cruzamentos/Jogo e Posse de Bola (%).
- **Radar Tático Multidimensional de 8 Eixos:** Normalização relativa das dimensões ofensivas e territoriais.
- **Decomposição Waterfall:** Visualização em cascata do que explica a diferença de xG entre o Cenário A e o Cenário B.
- **Mapas de Densidade 2D (KDE):** Comparação visual lado a lado da mancha de finalizações no gramado regulamentar.

---

## 📖 Rigor Metodológico em Todos os Módulos

Cada aba do sistema contém um **Guia Tático e Metodológico** estruturado em três pilares fundamentais:
1. **Qual pergunta queremos responder?** (O problema de negócio/futebol real investigado).
2. **Detalhamento das Variáveis e Dados** (Fórmulas, definições estatísticas e convenções espaciais da FIFA).
3. **O Mito Desmontado vs. A Realidade Tática** (O erro analítico comum cometido na mídia versus a leitura correta baseada em dados).

---

## 🚀 Como Executar o Projeto

### 1. Ativar o Ambiente Virtual

No Windows:
```powershell
.venv\Scripts\activate
```

### 2. Executar o Pipeline de Dados

Para reprocessar os dados com todas as estatísticas táticas e espaciais:
```powershell
python -m src.processing.pipeline
```

### 3. Iniciar o Dashboard Streamlit

```powershell
streamlit run app/streamlit_app.py
```

```powershell
streamlit run app/streamlit_app.py
```

O aplicativo abrirá automaticamente no navegador em `http://localhost:8501`.
