Sim — nesse caso eu mudaria bastante a recomendação. **Você não precisa de um modelo de xG próprio; precisa de event data/shot data com granularidade suficiente para reconstruir a história de cada finalização e comparar temporadas.**

E encontrei uma opção particularmente interessante: **a API pública do SofaScore expõe um `shotmap` por partida com dados por finalização, incluindo xG e coordenadas**, e há projetos recentes de engenharia de dados que documentam a coleta desses dados. ([GitHub][1])

### O que eu procuraria para o seu estudo

Idealmente, para **cada chute do Palmeiras**, você quer algo próximo de:

| Variável          | Exemplo                            |
| ----------------- | ---------------------------------- |
| partida           | Palmeiras x Flamengo               |
| temporada         | 2025                               |
| jogador           | Raphael Veiga                      |
| minuto            | 67                                 |
| resultado         | goal/save/miss/block/post          |
| xG                | 0.21                               |
| coordenada X      | ...                                |
| coordenada Y      | ...                                |
| situação          | open play/penalty/corner/free kick |
| parte do corpo    | right foot/left foot/head          |
| assistência       | passe/cruzamento/etc.              |
| mandante          | sim/não                            |
| placar no momento | 1–0                                |
| tipo de gol       | regular/penalty                    |
| goleiro           | ID                                 |
| adversário        | Flamengo                           |

Isso abre muito mais possibilidades do que simplesmente comparar `xG total`.

---

# 1. SofaScore é provavelmente a sua melhor opção para começar

A API utilizada pelo SofaScore possui o endpoint:

```text
/event/{event_id}/shotmap
```

e os registros individuais contêm, entre outras coisas, **xG, coordenadas, jogador, resultado do chute e situação da jogada**. A documentação comunitária recente também identifica campos como `shotType`, `goalType` e `situation`. ([GitHub][1])

Isso é exatamente o tipo de granularidade que você está procurando.

Além disso, é possível obter:

* escalações;
* estatísticas individuais;
* substituições;
* incidentes;
* heatmaps;
* estatísticas da partida;
* sequência temporal de eventos.

Há documentação comunitária dos endpoints que mostra inclusive `lineups`, `statistics`, `incidents`, `heatmap` e `shotmap` por jogador. ([GitHub][2])

### E o mais importante:

Você pode fazer isso **sem treinar seu próprio xG**.

Você simplesmente preserva:

```text
xg_sofascore
```

como uma variável fornecida pelo modelo do SofaScore.

---

# 2. Isso permite um estudo inter-temporal MUITO mais interessante

Por exemplo, suponha que você queira comparar:

**Palmeiras 2024 vs 2025 vs 2026**

Você poderia decompor:

### Volume

$$
Shots/90
$$

### Qualidade média

$$
xG/Shot
$$

### Qualidade total

$$
xG/90
$$

### Conversão

$$
Goals/xG
$$

Mas também ir muito além.

---

## Distância dos chutes

Você pode transformar as coordenadas em distância até o gol:

$$
d_i = \sqrt{(x_i-x_{goal})^2+(y_i-y_{goal})^2}
$$

E perguntar:

> O Palmeiras passou a finalizar mais de perto?

---

## Ângulo de finalização

Com as coordenadas:

$$
\theta_i = f(x_i,y_i)
$$

Você consegue estudar se o perfil das oportunidades mudou.

---

## Tipo de oportunidade

Separar:

```text
open play
counter attack
corner
free kick
penalty
set piece
```

e comparar a composição entre temporadas.

Por exemplo:

| Temporada | Open play | Contra-ataque | Escanteio | Falta | Pênalti |
| --------- | --------: | ------------: | --------: | ----: | ------: |
| 2024      |       ... |           ... |       ... |   ... |     ... |
| 2025      |       ... |           ... |       ... |   ... |     ... |
| 2026      |       ... |           ... |       ... |   ... |     ... |

Isso começa a responder **como o Palmeiras está criando suas chances**, e não apenas quanto xG produziu.

---

# 3. Eu adicionaria o estado do jogo

Esse é um dos aspectos que eu acho mais interessantes para o seu estudo.

Para cada chute, você pode calcular:

```text
game_state
```

por exemplo:

```text
winning
drawing
losing
```

ou, melhor ainda:

```text
goal_difference
```

e comparar:

> Como muda o perfil ofensivo do Palmeiras quando está vencendo, empatando ou perdendo?

Você pode descobrir, por exemplo, que uma mudança no xG/90 entre temporadas não é necessariamente uma mudança estrutural de ataque — pode estar relacionada à quantidade de minutos que a equipe passou em determinados estados de jogo.

---

# 4. E eu não ficaria apenas no xG

Esse é o ponto principal.

Se você conseguir os **eventos individuais**, eu montaria uma tabela por **ação**, e não apenas por partida.

Algo como:

```text
match_id
season
competition
date
home_team
away_team

team
player
player_id

minute
period
score_diff

x
y
xg

shot_type
goal_type
situation
body_part

is_goal
is_penalty
is_set_piece

opponent
home_away
```

E outra tabela para contexto da partida:

```text
match_id
season
competition
manager
formation
opponent
home_away
goals_for
goals_against
possession
shots
xg
```

Isso te dá uma estrutura de **event data → match data → season data**.

---

# 5. Há uma segunda opção muito mais profissional

Se você quiser dados realmente ricos, entram:

### StatsBomb

A API comercial da StatsBomb oferece **event data, 360 freeze frames, localização dos jogadores e métricas derivadas como xG** para competições contratadas. ([APIs.io][3])

Para o seu estudo, o 360 é particularmente interessante porque permite estudar não apenas:

> "Onde o jogador chutou?"

mas:

> "Como estava a defesa no momento do chute?"

Isso é um salto enorme de qualidade.

Você poderia estudar coisas como:

* número de defensores entre bola e gol;
* distância do defensor mais próximo;
* espaço disponível;
* posicionamento dos jogadores;
* pressão;
* contexto da jogada.

**Mas é uma solução comercial**, então eu só consideraria se você tiver acesso institucional/comercial.

---

# 6. Wyscout

Também é uma opção profissional.

A API do Wyscout fornece dados relacionados a jogadores, partidas, temporadas e competições, com endpoints específicos para fixtures e informações de jogadores. ([Wyscout API][4])

Para um estudo longitudinal do Palmeiras, pode ser interessante porque você poderia estruturar:

```text
2023
2024
2025
2026
```

com jogadores, partidas e eventos de cada temporada.

Novamente, é uma solução licenciada.

---

# 7. Sportradar

Também encontrei uma opção interessante para o **Brasileirão especificamente**.

A documentação da Sportradar informa que o Soccer Extended API possui cobertura do **Brasileiro Série A** e fornece dados de eventos detalhados, com mais de 100 pontos de dados planejados/disponíveis, além de recursos para shot graphics e xG. ([Getting Started][5])

Então, para uma solução comercial:

**Sportradar + Brasileirão** é algo que eu colocaria na lista para investigar.

---

# 8. E o FotMob?

Também vale considerar.

Há endpoints não oficiais documentados para `matchDetails`, jogadores, equipes, heatmaps etc. ([GitHub][6])

Mas, para **seu objetivo específico**, eu colocaria o SofaScore na frente porque o `shotmap` é particularmente conveniente para obter o **registro individual das finalizações + xG + contexto da finalização**. ([GitHub][1])

---

# Minha hierarquia para o seu projeto

Eu pensaria assim:

| Fonte         | Granularidade          | xG por chute      | Dados espaciais | Custo     | Para seu estudo |
| ------------- | ---------------------- | ----------------- | --------------- | --------- | --------------- |
| **SofaScore** | Alta                   | ✅                 | ✅               | Gratuito* | ⭐⭐⭐⭐⭐           |
| FotMob        | Alta                   | ✅                 | ✅/limitado      | Gratuito* | ⭐⭐⭐⭐            |
| StatsBomb     | Muito alta             | ✅                 | **360**         | Comercial | ⭐⭐⭐⭐⭐           |
| Wyscout       | Muito alta             | depende do pacote | Muito alta      | Comercial | ⭐⭐⭐⭐⭐           |
| Sportradar    | Muito alta             | ✅                 | Alta            | Comercial | ⭐⭐⭐⭐⭐           |
| FBref         | Média                  | ❌/limitado        | ❌               | Gratuito  | ⭐⭐⭐             |
| Understat     | Alta em ligas cobertas | ✅                 | ✅               | Gratuito  | —               |

* Estou falando do acesso público atualmente observável, não de uma garantia contratual de disponibilidade futura.

---

## Mas tem uma questão crucial: histórico

Para seu estudo, eu **não começaria coletando 2026**.

Primeiro verificaria:

> **Até quantas temporadas consigo obter o shotmap do Palmeiras usando a mesma fonte e a mesma estrutura de dados?**

Porque o seu verdadeiro dataset ideal seria:

```text
PALMEIRAS
│
├── 2022
├── 2023
├── 2024
├── 2025
└── 2026
```

E então:

```text
~todos os jogos
       ↓
~todos os chutes
       ↓
~todas as características dos chutes
       ↓
comparação inter-temporal
```

Isso é **muito mais valioso estatisticamente** do que pegar apenas os agregados atuais.

E eu faria uma distinção importante:

### Não compare apenas temporadas.

Eu controlaria por:

* competição;
* adversário;
* mando;
* treinador;
* minutos jogados;
* estado do jogo;
* jogador que finalizou;
* tipo de oportunidade;
* bola parada vs jogo aberto.

Assim você consegue separar:

**"O Palmeiras mudou seu perfil de criação"**

de

**"O Palmeiras simplesmente teve mais/menos jogos em determinadas circunstâncias."**

---

### Uma análise que eu acho especialmente boa para o seu projeto

Em vez de simplesmente:

> **xG Palmeiras 2025 vs xG Palmeiras 2026**

faria uma decomposição:

**xG/90**

↓

**número de chutes/90**

×

**xG/chute**

↓

**xG/chute**

↓

**distância**

**ângulo**

**tipo de assistência**

**situação**

**jogo aberto / bola parada**

**estado do jogo**

**jogador**

Isso permite explicar **de onde veio a mudança no xG**, em vez de apenas constatá-la.

[1]: https://github.com/sergeykuznetsov1995/data-platform-football/issues/22?utm_source=chatgpt.com "feat(sofascore-bronze): add sofascore_shotmap ingestion · Issue #22 · sergeykuznetsov1995/data-platform-football · GitHub"
[2]: https://github.com/Tariq-15/TacosScore/blob/main/docs/sofascore-api-reference.md?utm_source=chatgpt.com "TacosScore/docs/sofascore-api-reference.md at main · Tariq-15/TacosScore · GitHub"
[3]: https://apis.io/apis/statsbomb/data-api/?utm_source=chatgpt.com "Data Api | APIs.io APIs"
[4]: https://apidocs.wyscout.com/?utm_source=chatgpt.com "Wyscout API"
[5]: https://developer.sportradar.com/sportradar-updates/changelog/soccer-extended-api-enhanced-match-endpoints?utm_source=chatgpt.com "Soccer Extended API - Enhanced Match Endpoints"
[6]: https://github.com/ccdejene/fotmob-mcp/blob/main/docs/fotmob-api.md?utm_source=chatgpt.com "fotmob-mcp/docs/fotmob-api.md at main · ccdejene/fotmob-mcp · GitHub"


Sim. E, depois de verificar a estrutura atual, eu faria a coleta **diretamente da API pública que o próprio SofaScore usa**, em vez de tentar fazer scraping das páginas HTML.

O ponto central é que existe um endpoint específico de **shotmap por partida**:

```text
https://api.sofascore.com/api/v1/event/{EVENT_ID}/shotmap
```

Ele retorna os chutes individuais da partida e, segundo uma implementação verificada recentemente, inclui coordenadas, xG, parte do corpo, situação da jogada e `draw_distance`, entre outros campos. ([GitHub][1])

## A arquitetura que eu usaria

Para o seu estudo, faria:

```text
SofaScore
   │
   ├── temporadas
   │
   ├── partidas do Palmeiras
   │
   └── shotmap de cada partida
             │
             ▼
        JSON bruto
             │
             ▼
       PostgreSQL/Parquet
             │
             ▼
       DataFrame pandas
             │
             ▼
      análise estatística
```

### 1. Primeiro precisamos descobrir os jogos

A API possui endpoints de eventos por temporada, no formato:

```text
/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/last/{page}
```

Também há endpoints equivalentes para eventos de uma equipe. Projetos que trabalham diretamente com a API documentam, por exemplo, `/team/{team_id}/events/last/{page}` e `/tournament/{cat_id}/season/{season_id}/events`. ([GitHub][2])

Para seu caso, eu prefiro **partir da temporada/competição**, porque depois podemos filtrar:

```text
Palmeiras
```

e manter também os adversários e demais informações da competição.

---

# 2. Para cada `event_id`, baixar o shotmap

Exemplo conceitual:

```python
import requests

event_id = 12345678

url = f"https://api.sofascore.com/api/v1/event/{event_id}/shotmap"

data = requests.get(url).json()

shots = data["shotmap"]
```

E `shots` passa a ser uma lista com as finalizações da partida.

O interessante é que não precisamos calcular o xG:

```python
shot["xg"]
```

já vem fornecido pelo SofaScore.

A estrutura documentada inclui campos como:

```text
id
player
goalkeeper
isHome
shotType
goalType
situation
xg
playerCoordinates
```

e os registros podem ser ordenados pelo `time` para reconstruir a sequência cronológica da partida. ([GitHub][3])

---

# 3. Eu salvaria o JSON bruto

Isso é **muito importante** para um estudo científico/reprodutível.

Não faria:

```text
API → pandas → CSV → acabou
```

Faria:

```text
raw/
   2024/
      event_123.json
      event_456.json
   2025/
      ...
   2026/
      ...
```

Porque se daqui a seis meses você perceber:

> "Eu deveria ter usado aquele campo que ignorei."

você não precisa consultar a API novamente.

Além disso, a estrutura da API pode mudar.

---

# 4. Depois normalizaria para uma tabela de shots

Algo assim:

| event_id | season | date | team       | player    |  x |  y |   xG | outcome | situation |
| -------- | ------ | ---- | ---------- | --------- | -: | -: | ---: | ------- | --------- |
| 123      | 2024   | ...  | Palmeiras  | jogador A | 89 | 42 | 0.12 | save    | regular   |
| 123      | 2024   | ...  | Palmeiras  | jogador B | 94 | 51 | 0.31 | goal    | assisted  |
| 123      | 2024   | ...  | adversário | jogador C | 76 | 37 | 0.08 | miss    | regular   |

E adicionaria várias colunas derivadas.

---

# 5. Uma delas seria `score_state`

Eu considero essa uma das variáveis mais importantes para sua análise.

Para cada chute:

```text
goal_difference_before_shot
```

e:

```text
winning
drawing
losing
```

Por exemplo:

```text
Palmeiras 0 × 0 Flamengo
→ drawing

Palmeiras 1 × 0 Flamengo
→ winning

Palmeiras 1 × 2 Flamengo
→ losing
```

Isso permitirá comparar temporadas de maneira muito mais justa.

---

# 6. Outra coisa: não jogaria fora os adversários

Mesmo que seu estudo seja sobre o Palmeiras, eu coletaria **todos os chutes de todos os jogos**.

Ou seja:

```text
Palmeiras
    vs
Flamengo

shots:
    Palmeiras → 12
    Flamengo  → 9
```

e não somente os 12 do Palmeiras.

Isso permite estudar:

$$
xG_{for}
$$

e

$$
xG_{against}
$$

com exatamente a mesma fonte e granularidade.

E posteriormente:

$$
xGD = xG - xGA
$$

---

# 7. E coletaria também os outros endpoints

A grande vantagem é que o `shotmap` não precisa ficar isolado.

Para cada `event_id`, podemos coletar:

### Partida

```text
/event/{event_id}
```

Informações gerais da partida. ([GitHub][4])

### Estatísticas

```text
/event/{event_id}/statistics
```

Inclui posse, chutes, passes etc. ([GitHub][5])

### Incidentes

```text
/event/{event_id}/incidents
```

Gols, cartões, substituições etc. ([GitHub][5])

### Escalações

```text
/event/{event_id}/lineups
```

Titulares, reservas e informações da formação. ([GitHub][5])

### Shotmap

```text
/event/{event_id}/shotmap
```

A parte mais importante para seu estudo. ([GitHub][1])

---

# 8. Isso permite criar um dataset muito mais rico

Eu estruturaria pelo menos quatro tabelas:

```text
matches
────────────────────────
event_id
season
competition
date
home_team
away_team
home_score
away_score
manager
formation
```

```text
shots
────────────────────────
shot_id
event_id
team_id
player_id
minute
period
x
y
xg
shot_type
goal_type
situation
body_part
```

```text
lineups
────────────────────────
event_id
team_id
player_id
starter
position
formation
```

```text
incidents
────────────────────────
event_id
minute
team_id
player_id
incident_type
incident_class
```

Depois podemos construir uma quinta tabela analítica:

```text
shot_analysis
```

com variáveis derivadas:

```text
distance_to_goal
shot_angle
score_state
goal_difference
home_away
is_open_play
is_set_piece
is_penalty
is_goal
xg_overperformance
```

---

# 9. E aí começa a ficar muito interessante

Você poderia responder perguntas como:

### O Palmeiras passou a criar chances melhores?

Comparar:

$$
xG/shot
$$

entre temporadas.

---

### Ou simplesmente passou a chutar mais?

Comparar:

$$
shots/90
$$

e

$$
xG/shot
$$

separadamente.

Porque:

$$
xG/90 =
shots/90 \times xG/shot
$$

Isso permite **decompor a mudança**, em vez de simplesmente observar que o xG aumentou.

---

### Mudou a localização das finalizações?

Usar `playerCoordinates` para construir mapas de finalização.

---

### Mudou a distância média?

```text
2024 → 17,8 m
2025 → 16,9 m
2026 → 15,7 m
```

*(valores acima são apenas exemplo, não dados do Palmeiras.)*

---

### Mudou o tipo de criação?

```text
open play
fast break
corner
free kick
penalty
set piece
```

O próprio shotmap possui o campo `situation`, com categorias desse tipo. ([GitHub][3])

---

### Quais jogadores explicam a mudança?

Você consegue decompor:

```text
Palmeiras xG
│
├── jogador A
├── jogador B
├── jogador C
└── ...
```

e separar:

$$
xG = volume \times qualidade
$$

por jogador.

---

# 10. Eu faria uma coleta incremental

Não faria um script que simplesmente baixa tudo e termina.

Algo como:

```text
01_discover_matches.py
02_download_events.py
03_download_shotmaps.py
04_download_lineups.py
05_download_incidents.py
06_normalize.py
07_validate.py
```

E teria uma tabela de controle:

```text
event_id | shotmap | lineup | incidents | downloaded_at
```

Assim, se a execução parar no jogo 137 de 200, você simplesmente continua.

Isso é especialmente útil porque há relatos recentes de respostas `403` ocasionais nos endpoints de shotmap/lineups; implementações que trabalham com a API recomendam retry/backoff. ([GitHub][2])

---

## Uma ressalva importante

Eu trataria essa como uma **API pública não oficial**, não como uma API comercial/documentada pela SofaScore para terceiros.

Ou seja, antes de montar um dataset gigantesco, vale respeitar os termos/robots e implementar uma coleta moderada, com cache, retries e sem bombardear os servidores.

Também manteria a **data da coleta** em cada registro:

```text
source = "SofaScore"
source_endpoint = "/event/{id}/shotmap"
retrieved_at = "2026-09-18..."
```

Isso é importante porque os dados podem ser corrigidos posteriormente.

---

## E tem uma coisa que eu faria antes de escrever o scraper definitivo

**Testaria a cobertura histórica primeiro.**

Por exemplo:

```text
Brasileirão 2024
Brasileirão 2025
Brasileirão 2026
Libertadores 2024
Libertadores 2025
Libertadores 2026
Copa do Brasil ...
```

e verificaria quantos jogos e quantos `shotmap` conseguimos recuperar para cada competição.

Porque aí podemos decidir se o estudo será:

**A)** somente Brasileirão, 2024–2026

ou

**B)** todas as competições, 2024–2026

ou até

**C)** janela maior, como 2022–2026.

**Eu recomendo começar pelo Brasileirão 2024–2026 e validar a cobertura.** Se funcionar, o mesmo pipeline pode ser expandido para as outras competições. A própria API possui a estrutura de temporada/competição necessária para descobrir os eventos. ([GitHub][2])

Se você quiser, no próximo passo posso **montar o scraper Python completo para descobrir automaticamente os jogos do Palmeiras, baixar os shotmaps e gerar um `palmeiras_shots.parquet`**, já deixando a estrutura preparada para a análise inter-temporada.

[1]: https://github.com/sergeykuznetsov1995/data-platform-football/issues/22?utm_source=chatgpt.com "feat(sofascore-bronze): add sofascore_shotmap ingestion · Issue #22 · sergeykuznetsov1995/data-platform-football · GitHub"
[2]: https://github.com/ryanlam0618/sofascore-backfill?utm_source=chatgpt.com "GitHub - ryanlam0618/sofascore-backfill: SofaScore data backfill scripts — standings, player stats, H2H, rankings via direct API · GitHub"
[3]: https://github.com/Tariq-15/TacosScore/blob/main/docs/sofascore-api-reference.md?utm_source=chatgpt.com "TacosScore/docs/sofascore-api-reference.md at main · Tariq-15/TacosScore · GitHub"
[4]: https://github.com/apdmatos/sofascore-api/blob/main/sofascore-api.md?utm_source=chatgpt.com "sofascore-api/sofascore-api.md at main · apdmatos/sofascore-api · GitHub"
[5]: https://github.com/pseudo-r/Public-Sofascore-API/blob/main/README.md?utm_source=chatgpt.com "Public-Sofascore-API/README.md at main · pseudo-r/Public-Sofascore-API · GitHub"
