# CONTEXTO — ANS / Panorama da Saúde Suplementar no Brasil

Ponto de entrada único para entender o projeto e consultar fatos sem reler tudo.
Documentação detalhada fica nos arquivos apontados em **§12 Índice**. Se este arquivo divergir dos detalhes, vale o detalhe (e este arquivo deve ser corrigido).

---

## 1. Objetivo

Construir uma base analítica da saúde suplementar no Brasil a partir do **ANS TabNet** e entregá-la como **dashboard Power BI** sobre um modelo semântico que impede dupla contagem.

- Camada analítica (`raw/` → `tidy/` → `curated/`): **concluída e validada**.
- Camada Power BI (`powerbi/ANS_Panorama`): **modelo e relatório autorados** (4 páginas, 38 medidas), com os números **validados por DAX** contra os CSVs (27/10/2026, §6.1). Em andamento: redesenho visual (tema, layout e novas páginas); os defeitos visuais conhecidos estão em §7.

## 2. Fonte e janela temporal

- **Fonte única:** ANS TabNet (interface web), 6 consultas `.def`, botão *"Copia como .CSV"*. Sem API, FTP ou repositório alternativo.
- **Origem declarada:** `SIB/ANS/MS – 08/2026` (beneficiários e cobertura); `ANS – 2º trim/2026, corte 25/08/2026` (receitas).
- **Coleta:** 16/10/2026 (re-extração integral; 29 arquivos byte a byte idênticos à coleta original de 14/10/2026 perdida).
- **Janela:** 21 competências **trimestrais** (Jun/2021 → Jun/2026); **anual** 2021→2026 (cobertura e receitas); snapshot **Ago/2026** (operadoras ativas). **NÃO existe dado mensal** no TabNet (L1).
- **2026 é parcial** (corte ago/2026 para cobertura, 2º trim/2026 para receitas): nunca tratar como ano fechado.

## 3. Mapa do repositório

| Pasta | Papel | Regra |
|---|---|---|
| `raw/` | evidência primária (29 CSVs originais) | **imutável** |
| `tidy/` | desempilhamento fiel (1 célula = 1 linha) | não interpreta geografia nem arredonda |
| `curated/` | modelo analítico (10 dims + 10 fatos) | onde as regras de negócio são aplicadas |
| `powerbi/ANS_Panorama/` | semantic model (TMDL) + relatório (PBIR) | consome `curated/` |
| `meta/` | extrator TabNet, gerador do `tidy`, inventário e validadores da Fase 1 |
| `inventario/` | inventário das bases, relatório de qualidade (R1–R10, L1–L10), regras de chave geográfica |
| `scripts/`, `evals/`, `.agents/` | manutenção do toolkit de skills (não fazem parte da entrega de dados; ficam fora do repositório público via `.gitignore`) |
| `docs/img/` | capturas das 4 páginas do relatório usadas no `README.md` |

## 4. Convenções de dados

- CSV **UTF-8 com BOM**, separador `;`, **decimal com ponto**, sem separador de milhar, **vazio = nulo**.
- `vinculos` = inteiro (`Int64`); R$ e percentuais = decimal. Percentual em **pontos percentuais** (9 = 9%).
- **Nenhuma coluna `Total`** entrou na `curated` (o total é sempre recalculado).
- Chaves geográficas **canônicas** com prefixo de tipo: `UF:`, `MUN:`, `CAP:`, `REG:`, `OPER:`, `MODAL:`, `PART:`, `PSEUDO:` — nunca juntar por texto cru.

## 5. Modelo analítico (`curated/`)

### Dimensões

| Dimensão | Grão | Chave | Nota |
|---|---|---|---|
| `dim_periodo` | 34 períodos | `periodo_id` | 21 trimestrais, 6 anuais com mês, 6 anuais sem mês, 1 snapshot; `tipo_granularidade` ∈ {trimestral, anual, snapshot}; `ordem` = AAAAMM |
| `dim_uf` | 28 | `UF:<2>` | 27 UFs + `UF:00` resíduo; `tipo` ∈ {real, pseudo} |
| `dim_regiao` | 6 | `REG:<nn>` | 5 regiões + Não Identificado; `tipo` ∈ {regiao, pseudo} |
| `dim_municipio` | 5.599 | `MUN:<6>` / `PSEUDO:` | 5.570 IBGE + Boa Esperança do Norte + resíduos |
| `dim_capital` | 27 | `CAP:<nn>` | nome → `municipio_id` |
| `dim_operadora` | 1.201 | `OPER:<6>` | união de 3 fontes + `PSEUDO:sem_correspondencia` |
| `dim_modalidade` | 9 | `MODAL:<nome>` | 8 reais + "não informada" |
| `dim_recorte_membro` | 80 | `(recorte, membro_id)` | membros de sexo, faixa etária, tipo de contratação, segmentação, modalidade, grande região, faixa×sexo |
| `dim_particao` | 2 | `PART:capital`/`interior` | eixo paralelo, **não soma** com UF |
| `dim_medida` | 11 | `medida_id` | catálogo de aditividade por coluna |

### Fatos (grão · medidas · aditividade)

| Fato | Grão | Medida(s) | Aditiva? |
|---|---|---|---|
| `fato_beneficiarios_uf_competencia` | UF × competência | `vinculos_assistencia_medica`, `vinculos_excl_odontologico` | sim (cada) |
| `fato_beneficiarios_recorte_competencia` | nível(BRASIL/UF/REGIAO) × geo × recorte × membro × competência | `vinculos` | sim, **dentro do mesmo recorte/nível/geo** |
| `fato_beneficiarios_particao_competencia` | partição × competência | `vinculos` | sim |
| `fato_beneficiarios_capital_competencia` | capital × competência | `vinculos` | sim |
| `fato_beneficiarios_municipio_competencia` | município × competência | `vinculos` | sim |
| `fato_beneficiarios_operadora_competencia` | operadora × competência | `vinculos` | sim |
| `fato_taxa_cobertura_uf_ano` | UF × ano | `taxa_cobertura_pct` | **não** |
| `fato_taxa_cobertura_municipio_ano` | município × ano | `taxa_cobertura_pct` | **não** |
| `fato_receitas_operadora_ano` | operadora × ano | `receita_contraprestacoes_reais` | sim |
| `fato_receitas_modalidade_ano` | modalidade × ano | `receita_contraprestacoes_reais` | sim |

Total: 14.268 linhas de dados · 180.773 observações úteis · 16/16 + 17/17 + 29/29 validações OK.

## 6. Modelo semântico Power BI (`powerbi/ANS_Panorama/ANS_Panorama.SemanticModel`)

- **20 tabelas** (10 dims + 10 fatos), nomes em português, **25 relacionamentos** Many→One / OneDirection ativos (o 25º, `UF-capital`, liga `Capital.uf_id` a `UF`; `uf_id` é derivado no Power Query de `municipio_id`: `"UF:"` + dígitos 1–2 do código IBGE).
- Parâmetro/expressão `PastaCurated` aponta para `...\curated` (caminho local absoluto). Cada tabela lê um CSV de `curated\dims`/`curated\fatos` via `Csv.Document` + `Table.PromoteHeaders` + `Table.TransformColumnTypes(..., "en-US")`.
- `compatibilityLevel: 1700`, `language: 1046` (pt-BR na interface), `culture: en-US` (parsing M explícito), annotation `PBI_ProTooling = ["MCP-PBIModeling"]`.
- **39 medidas de negócio** + **9 de apresentação** (pasta `Apresentação`, tabela `Vínculos por UF e competência`: cabeçalhos e faixas de KPIs em HTML de cada página e o painel `Perfil HTML - UF`), todas em tabelas fato. Coluna nova `Operadora[Nome curto]` (razão social sem sufixo societário, caixa mista, derivada no Power Query) para rótulos. Colunas técnicas (`*_id`, chaves) ocultas.

### Regras de cálculo das medidas

1. **Estoque, nunca soma de trimestres.** Vínculo é um retrato do trimestre. As 8 medidas-base de vínculos (`Vínculos (assistência médica)`, `Vínculos (sem odontológico exclusivo)`, `Vínculos recorte (base)`, `Vínculos nas capitais`, `Vínculos municipais`, `Vínculos capital + interior`, `Vínculos das operadoras`, `Operadoras com vínculos`) calculam `_ord = MAX('Período'[Ordem])` entre os períodos **trimestrais** no filtro e avaliam a soma nessa `Ordem`. Com um trimestre no filtro (eixo da linha), o valor é o próprio trimestre; com "Todos" ou vários, é o trimestre mais recente do filtro. Antes desta regra, "Todos" somava 21 trimestres (1,07 bi em vez de 53 mi; corrigido em 27/10/2026).
2. **Medidas derivadas herdam a base.** Recortes, participações e comparações chamam as medidas-base; por isso só a base aplica a regra de estoque.
3. **Recorte e nível fixos.** Cada medida de recorte fixa `Recorte` e `Nível geográfico` com `CALCULATE`; sem o filtro geográfico aplicável, devolve vazio de propósito.
4. **Taxa não é aditiva.** `Taxa de cobertura (UF/município)` usa `SELECTEDVALUE` (vazio se houver mais de uma UF/município ou ano). A média simples usa o **ano de cobertura mais recente do filtro** (`periodo_id` máximo).
5. **Receita é fluxo anual**, somada por ano; os "últimos anos completos" usam `[Último ano completo]` (2025 enquanto o corte for ago/2026).
6. **Textos e rótulos** ignoram o filtro de período (`REMOVEFILTERS('Período')`) para não quebrar com o slicer.
7. **Formato:** medidas numéricas ficam numéricas (`formatString`); `FORMAT` só em rótulos de texto.

### Catálogo de medidas (38) — o que é e por que é assim

**Vínculos — total e período** (`Vínculos por UF e competência`)

| Medida | Lógica | Por quê |
|---|---|---|
| `Vínculos (assistência médica)` | soma do fato UF (28 códigos) na competência mais recente do filtro | base nacional aditiva por UF; inclui o resíduo `UF:00`, então fecha com o total da ANS |
| `Vínculos (sem odontológico exclusivo)` | idem, coluna `vinculos_excl_odontologico` | medida distinta; nunca somar com a anterior |
| `Última competência` | rótulo do maior `periodo_id` do fato, sem filtro de período | cabeçalho "Jun/26" estável |
| `Ano de corte dos dados` | ano do maior período de cobertura | 2026 = corte ago/2026 |
| `Último ano completo` | ano do corte se dezembro; senão ano − 1 | evita comparar 2026 parcial com anos fechados (= 2025) |
| `Nota de período parcial` | texto com ano e rótulo do corte | aviso fixo de parcialidade |
| `Vínculos - última competência` | total na competência mais recente global | KPI que não varia com o slicer |
| `Vínculos - mesma competência do ano anterior` | mesmo total em `Ordem − 100` | alinha por `Ordem` (AAAAMM), não por rótulo |
| `Variação anual de vínculos` | (última − ano anterior) ÷ ano anterior | comparação anual alinhada |
| `Participação da UF no total` | UF ÷ total sem filtro de UF | usar com UF no eixo |

**Vínculos por recorte** (`Vínculos por recorte`): `Vínculos recorte (base)` (oculta; soma crua de recortes sobrepostos, **não usar em visual**); `Vínculos por sexo`, `por faixa etária`, `por faixa etária e sexo`, `por modalidade`, `por segmentação`, `por tipo de contratação` (nível BRASIL), `por tipo de contratação por UF` (nível UF), `por grande região` (nível REGIAO); `Diferença recorte vs total UF` (teste de reconciliação: recorte sexo − total UF na mesma competência; **deve ser 0**). Cada uma fixa um recorte e um nível: a soma dos membros de **um** recorte reproduz o total nacional; recortes diferentes não se somam.

**Território**

| Medida | Tabela | Lógica |
|---|---|---|
| `Vínculos nas capitais` | `Vínculos por capital` | soma das 27 capitais (subconjunto) na competência mais recente do filtro |
| `Participação da capital no total` | idem | capitais ÷ total nacional (UF), sem filtro de `Capital` |
| `Vínculos municipais` | `Vínculos por município` | inclui resíduos (ignorado na UF, exterior, provisório) |
| `Vínculos municipais - territórios` | idem | só `Município[Tipo] = "municipio"` |
| `Vínculos municipais - resíduos` | idem | `Tipo <> "municipio"` |
| `Vínculos capital + interior` | `Vínculos por partição` | partição Capital × Interior (soma o total nacional) |
| `Participação da partição` | idem | partição ÷ total |

**Operadora / receita**

| Medida | Tabela | Lógica |
|---|---|---|
| `Vínculos das operadoras` | `Vínculos por operadora` | soma das operadoras na competência mais recente do filtro (fecha com o total UF) |
| `Operadoras com vínculos` | idem | `DISTINCTCOUNT` das operadoras com **vínculos > 0** na competência mais recente do filtro (662 em Jun/26; 704 em Jun/21). O fato traz 758 operadoras em todo trimestre, inclusive linhas zeradas (96 em Jun/26); até 27/10/2026 a medida contava as zeradas e mostrava 758 |
| `Participação da operadora` | idem | operadora ÷ total, sem filtro de `Operadora` |
| `Vínculos das operadoras - ano anterior` | idem | soma em `Ordem − 100` da competência mais recente do filtro (base da variação em 12 meses por operadora; criada em 27/10/2026) |
| `Receita de contraprestações (operadora)` | `Receitas por operadora e ano` | soma anual; o visual precisa filtrar `anual` |
| `Receita - último ano completo` | idem | `Ano = [Último ano completo]` (2025) |
| `Receita - ano anterior` | idem | `Ano = [Último ano completo] − 1` (2024) |
| `Variação anual de receita` | idem | (último − anterior) ÷ anterior |
| `Receita de contraprestações (modalidade)` | `Receitas por modalidade e ano` | soma anual por modalidade (mesma massa da operadora; não somar as duas) |

**Cobertura**: `Taxa de cobertura (UF)` e `Taxa de cobertura (município)` (`SELECTEDVALUE`, vazio se agregado — comportamento intencional); `Média simples das taxas (UF)` (média das UFs no **ano mais recente do filtro**; **não** é a taxa nacional ponderada).

### 6.1 Validação por DAX (27/10/2026, modelo ao vivo no Desktop)

Todas as 38 medidas avaliam sem erro (as de taxa devolvem vazio sem UF/município selecionado, como projetado). Valores de referência em Jun/26, sem filtros:

| Verificação | Resultado |
|---|---|
| Total de vínculos (AM) = soma UF = soma operadoras = município (terr. + resíduos) = capital + interior | **53.055.406** |
| Sexo, faixa etária, faixa × sexo, modalidade, segmentação, tipo de contratação (BRASIL e soma das UFs), grande região | cada um = 53.055.406 |
| `Diferença recorte vs total UF` | 0 |
| Sem odontológico exclusivo | 36.736.226 |
| Mesma competência do ano anterior (Jun/25) / variação | 52.340.620 / +1,37% |
| Capitais / participação | 20.299.496 / 38,26% (capital de SP 5.948.123; UF SP 18.601.228) |
| Resíduos municipais | 49.715 = 46.910 (`ignorado_exterior`, mesma massa de `UF:00`) + 2.798 (`ignorado_uf`) + 7 (provisório) |
| Operadoras com vínculos (> 0) | 662 (corrigido em 27/10/2026; antes contava 758 com linhas zeradas) |
| Receita 2025 / 2024 / variação | R$ 344.635.631.620 / R$ 312.087.070.950 / +10,43% |
| Média simples das taxas (UF), ago/2026 | 18,19% (confere com o CSV) |
| Receita total operadora × modalidade (6 anos) | diferem em R$ 44 de R$ 1,60 tri (≤ R$ 15 por ano; provável arredondamento da fonte — inferência, não é erro de carga) |

## 7. Relatório Power BI (`ANS_Panorama.Report`)

Tema base `CY26SU10` + tema próprio `ANSPanorama` (claro); canvas 1280×720, `FitToPage`; `pageOrder` definido. Visuais personalizados: HTML Content (Secure) e Deneb. 4 páginas:

| Página | ID | Visuais |
|---|---|---|
| **Visão geral** | `b3570a60a7124608b862` | 7 — **finalizada (27/10/2026)**: cabeçalho HTML com frase-resumo dinâmica, navegador de páginas, faixa de 4 KPIs em HTML Content (vínculos, receita, operadoras, cobertura, com variação e mini-série), série trimestral (Deneb), "Onde estão os vínculos" por grande região e "Capitais e interior" (Deneb), composições de tipo de contratação e modalidade (Deneb). Sem mapa: a geografia detalhada fica só na página Território |
| **Território** | `71c2a4e6b8d09f3a1c02` | 6 — **redesenhada (27/10/2026)**: cabeçalho HTML (concentração e amplitude da cobertura), navegador, 4 KPIs em HTML Content (região líder e participação, capitais, maior e menor cobertura), cartograma compacto de cobertura (Deneb), halteres de cobertura primeiro × último ano por UF com média das UFs (Deneb, com destaque da UF clicada), painel "Perfil da UF" em HTML Content (Brasil por padrão; UF clicada no mapa). Clique no mapa: filtra o perfil, destaca os halteres e não altera cabeçalho, navegador nem KPIs |
| **Perfil dos vínculos** (antiga Carteiras e vínculos) | `d2b8f6a1c3e45d9f0b12` | 5 — **redesenhada (27/10/2026)**: cabeçalho HTML, navegador, 4 KPIs em HTML Content (mulheres, 60+, até 19 anos, segmentação hospitalar e ambulatorial — participação, variação em p.p. desde Jun/21 e série), pirâmide etária por sexo (Deneb, eixo simétrico, faixa inconsistente em nota) e tipo de contratação por UF em 100% empilhado (Deneb, ordenado pelo peso do individual). Contratação e modalidade nacionais ficam só na Visão geral |
| **Operadoras e mercado** (antiga Financeiro e cobertura) | `e3c9a7b2d4f56e0a1c23` | 6 — **redesenhada (27/10/2026)**: cabeçalho HTML, navegador, 4 KPIs em HTML Content (operadoras com vínculos, participação das 5 maiores, HHI, receita por vínculo), ranking das 15 maiores operadoras com participação e variação em 12 meses (Deneb; demais operadoras somadas em nota), curva de concentração acumulada em escala log (Deneb) e receita de contraprestações por modalidade nos anos completos (Deneb). A cobertura migrou para a página Território |

**Defeitos visuais de 27/10/2026 — todos resolvidos no redesenho:** cobertura vazia com UF "Todos", receita por modalidade somando 2026 parcial, card "2 Mil", eixos em "Tri" e "Até 1 ano" ausente na faixa × sexo saíram junto com os visuais antigos.

**Filtros de visual obrigatórios** (proteção contra dupla contagem, embutidos no PBIR):
- Linha de vínculos: `Período[Tipo de granularidade] = "trimestral"`.
- Donut de modalidade: `Recorte de vínculos[Recorte] = "modalidade"`.
- Barra de grande região: `Região[Tipo] = "regiao"`.
- Barras de tipo de contratação: `Recorte de vínculos[Recorte] = "tipo_contratacao"`.
- Slicer/UF e eixo de UF: `UF[Tipo] = "real"`.
- Visuais financeiros e de cobertura: `Período[Tipo de granularidade] = "anual"`.

## 8. Regras de negócio — o que NÃO somar (crítico)

1. Não somar `vinculos_assistencia_medica` + `vinculos_excl_odontologico` (medidas distintas).
2. Não somar fatos de **grãos diferentes** (UF, município, operadora, capital, recorte) — dupla contagem.
3. Não somar **recortes diferentes** (ex.: masculino + faixa 10–14) — recortes se sobrepõem.
4. Não somar `Capital` + `Interior` com as linhas de **UF** (eixos paralelos).
5. Não somar as **27 capitais** esperando o total nacional (são subconjunto).
6. Não somar `taxa_cobertura_pct` (percentual, não aditivo).
7. Não somar as duas tabelas de receita (operadora + modalidade) — mesma massa.
8. Não somar receita de **2026** como ano completo (parcial).
9. Não cruzar vínculo (trimestral) com receita (anual) somando — alinhar época antes.
10. Não usar `membro`/texto como chave — usar sempre `*_id`.
11. Não tratar `PSEUDO:` como território em mapa; eles carregam massa e **não** podem ser descartados: no eixo UF, `UF:00` = 46.910 vínculos em Jun/26 (exterior/não identificado); no eixo município, 49.715 (46.910 + 2.798 ignorado na UF + 7 provisório).
12. **Não somar vínculos entre competências.** Vínculo é estoque; as medidas já aplicam a regra de estoque (§6), mas colunas cruas somadas em um visual ainda cometem o erro.

Medidas de recorte já fixam `recorte` + `nível geográfico`; sem o filtro geográfico aplicável, a medida retorna **vazio de propósito**.

## 9. Problemas conhecidos / riscos (resumo)

- **R1** colisões de rótulo (São Paulo/Rio = UF e capital; `XX0000 Município ignorado`) → resolvidas por chave canônica.
- **R2** linha `172208 Wanderlândia` no arquivo Centro-Oeste → entra como `PSEUDO:GO_municipio_nao_identificado` (valor preservado, sem atribuição).
- **R8** período/medida trocados no `tidy` da cobertura → corrigido no gerador.
- **L1** sem dado mensal · **L4** operadora sem cruzamento demográfico · **L5** cobertura é anual · **L6** receita: 1 de 7 contas, R$ correntes · **L9** sem validação externa.
- **Limitação atual:** taxa de cobertura pode passar de 100% (1 município) — razão beneficiários/população, não erro.
- **Sigla do DF (corrigido em 27/10/2026):** `dim_uf` derivava a sigla da linha `Município ignorado - UF`, inexistente para o DF (município único); `build_curated.py` passou a usar `SIGLA_SEM_IGNORADO = {'53': 'DF'}`. Só `dim_uf.csv` mudou; validações 16/16.
- **Pasta temporária** `.tmp-validation-curated/` na raiz: cópia de validação da `curated`, fora da entrega; avaliar remoção.
- **Salto em dez/21 na concentração:** a participação das 5 maiores operadoras passa de 28,8% (set/21) para 30,6% (dez/21) e o HHI de 223 para 245; é dado da fonte (provável reorganização societária entre grandes operadoras — inferência, não verificada).
- **Lição de TMDL (27/10/2026):** indentação mista (espaços no lugar de tab) em medida multilinha faz o parser incorporar `formatString`/`lineageTag` à expressão DAX (`SYNTAXERROR`, cards com erro). Ver `powerbi/ANS_Panorama/LEIA-ME.md` §5.

## 10. Como reproduzir

```bash
# pipeline de dados (a partir de raw/)
python meta/gera_tidy.py            # tidy/ (29)
python meta/validar_semantica.py    # 29/29 OK
python meta/gera_inventario.py
python meta/valida_fase1r.py        # 17/17 OK
python curated/scripts/build_curated.py
python curated/scripts/validar_curated.py   # 16/16 OK
```

Power BI:
- Abrir `powerbi/ANS_Panorama/ANS_Panorama.pbip` no Power BI Desktop (aplicativo da Store, Product Version 2.159.883.0).
- Validar o relatório: `powerbi-report-author.ps1 validate "<...>\ANS_Panorama.Report"` → 0 erros / 0 avisos.
- Gate de render: `powerbi-desktop.ps1 open "<...>\ANS_Panorama.pbip"` → `preview --host desktop` / `powerbi-desktop.ps1 screenshot-all`. (Ver `powerbi/ANS_Panorama/LEIA-ME.md` para detalhes e gotchas.)

## 11. Glossário

| Termo | Significado |
|---|---|
| Vínculo | relação de um beneficiário com um plano na competência (não é pessoa única) |
| AM / EO | Assistência Médica / Excluído odontológico-exclusivo |
| Competência | mês de referência trimestral (`T2021Q2`…`T2026Q2`) |
| Operadora | registro ANS de 6 dígitos |
| Modalidade | tipo da operadora (medicina de grupo, seguradora, etc.) |
| Segmentação | segmentação assistencial da operadora |
| Recorte | corte demográfico/contratual (sexo, faixa etária, tipo de contratação…) |
| Partição | Capital × Interior (eixo paralelo ao de UF) |
| Pseudo-membro | resíduo (`Não Identificado`, `Ignorado ou exterior`, provisório R2) — não é território |
| Taxa de cobertura | beneficiários ÷ população (%), anual, **não aditiva** |
| Contraprestação | receita do plano (1 das 7 contas de Receitas e Despesas), R$ correntes |
| Grão | conjunto de chaves que define a granularidade de um fato |

## 12. Índice da documentação

- `LEIA-ME.md` — visão geral do projeto, camadas e números-chave.
- `CONTEXTO.md` — **este arquivo** (entrada única para o agente).
- `curated/LEIA-ME.md` — modelo analítico completo (grãos, aditividade, cruzamentos válidos × inválidos).
- `inventario/inventario_bases.md` (+`.csv`/`.json`) — 29 bases com fonte, URL, eixo, cadência, período e linhas.
- `inventario/relatorio_qualidade.md` — achados R1–R10, validações e limitações L1–L10.
- `inventario/regras_chaves_geograficas.md` — chave `TIPO:CODIGO`, pseudo-membros e regras de junção.
- `powerbi/ANS_Panorama/LEIA-ME.md` — modelo semântico, relatório, autoria e validação do Power BI.
- `meta/extracao_log.jsonl` — log por consulta (data, duração, URL, bytes, SHA-256).
