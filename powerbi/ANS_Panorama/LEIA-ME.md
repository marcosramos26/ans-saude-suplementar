# Power BI — ANS_Panorama

Projeto Power BI (`.pbip`) que consome a camada `curated/` e entrega o panorama da saúde suplementar.
Semantic model em TMDL + relatório em PBIR (formato de arquivos texto, versionável).

- **Abrir:** `ANS_Panorama.pbip` no Power BI Desktop (app da Store, Product Version 2.159.883.0).
- **Estado (27/10/2026):** modelo e relatório carregam no Desktop; as 38 medidas foram **validadas por DAX** contra os CSVs (`../../CONTEXTO.md` §6.1) e as 4 páginas foram capturadas. O redesenho visual está em andamento — ver §6.

## 1. Estrutura do artefato

```
powerbi/ANS_Panorama/
├─ ANS_Panorama.pbip                        atalho do projeto (abre no Desktop)
├─ ANS_Panorama.SemanticModel/
│  ├─ definition.pbism                      (v4.2, qnaEnabled)
│  └─ definition/
│     ├─ database.tmdl                      compatibilityLevel 1700, language 1046
│     ├─ model.tmdl                         culture en-US; refs das 20 tabelas
│     ├─ expressions.tmdl                   parâmetro PastaCurated (caminho de curated/)
│     ├─ relationships.tmdl                 25 relacionamentos
│     └─ tables/*.tmdl                       20 tabelas (10 dims + 10 fatos)
└─ ANS_Panorama.Report/
   ├─ definition.pbir                       (byPath ../ANS_Panorama.SemanticModel)
   ├─ definition/
   │  ├─ version.json                        versões PBIR pinadas
   │  ├─ report.json                         tema base CY26SU10
   │  └─ pages/pages.json + <pageId>/page.json + <pageId>/visuals/<visualId>/visual.json
   └─ StaticResources/SharedResources/BaseThemes/CY26SU10.json
```

## 2. Modelo semântico

- **20 tabelas** (10 dimensões + 10 fatos), equivalentes 1:1 às tabelas de `curated/`.
- **25 relacionamentos** Many→One, direção única (fato → dimensão), todos ativos. Nunca há caminho fato→fato (isso é o que evita a dupla contagem).
- **`UF-capital`** (`Capital.uf_id` → `UF.uf_id`): `dim_capital.csv` não traz UF; a coluna `uf_id` é derivada no Power Query da partição `Capital` (`"UF:" & Text.Middle([municipio_id], 4, 2)`, pois `MUN:` + código IBGE de 6 dígitos começa pelo código da UF). Sem ela, o filtro de UF não chegava aos vínculos de capitais (todas as barras mostravam o total).
- Dados **em memória (Import)**; cada partição M lê o CSV correspondente:

  ```
  Csv.Document(File.Contents(PastaCurated & "\dims|fatos\<arquivo>.csv"),
      [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])
  → Table.PromoteHeaders
  → Table.TransformColumnTypes(..., "en-US")   // decimal com ponto forçado
  ```

- `PastaCurated` é um **parâmetro do Power Query** com o caminho absoluto da pasta `curated/` na máquina de quem abre o projeto. Ao clonar: abrir o `.pbip`, ir em *Transformar dados → Editar parâmetros*, apontar para `<clone>\curated` e clicar em *Atualizar*.
- Colunas técnicas (chaves `*_id`, `Nível geográfico`, `Ordem`) são **ocultas**; usuário final vê nomes de negócio.
- Para recarregar os dados sem a interface, é possível enviar um `refresh` TMSL ao Analysis Services local do Desktop (porta em `msmdsrv.exe`); a recarga lê só os CSVs de `curated/` e deixa o arquivo com "alterações não salvas" (salvar com Ctrl+S).

### Medidas (39 de negócio + 9 de apresentação, DAX)

Todas ficam nas tabelas fato e são documentadas em `../../CONTEXTO.md` §6. Princípios:

- **Nunca somar a coluna crua de um recorte/taxa.** Cada medida aplica `CALCULATE` fixando o recorte e o nível geográfico.
- **Vínculo é estoque (regra de 27/10/2026):** as 8 medidas-base de vínculos usam `VAR _ord = CALCULATE(MAX('Período'[Ordem]), 'Período'[Tipo de granularidade] = "trimestral")` e `CALCULATE(<soma>, 'Período'[Ordem] = _ord)`. Um trimestre no filtro devolve ele mesmo (eixo da linha); "Todos"/vários devolvem o mais recente do filtro. Antes, "Todos" somava 21 trimestres e inflava os gráficos ~20× (1,07 bi no lugar de 53 mi). Recortes, participações e comparações herdam a base.
- Medidas de retrato fixo (`Vínculos - última competência`, rótulos, notas) ignoram o filtro da página (`REMOVEFILTERS('Período')` + `LOOKUPVALUE`/`MAX`) para não "quebrar" com o slicer.
- `Média simples das taxas (UF)` usa o `periodo_id` máximo do filtro (não mistura anos).
- Medidas de taxa usam `SELECTEDVALUE` (devolvem vazio se o contexto agrega mais de uma UF/ano) — comportamento intencional de não-aditividade.
- `Vínculos recorte (base)` é **oculta** e serve só de base às medidas fixadas.
- Comparação anual de vínculos alinha pela `Ordem` (`_ord - 100`), não por rótulo.
- Rationale e lógica de cada uma das 38 medidas: `../../CONTEXTO.md` §6.

## 3. Relatório (4 páginas)

Tema base `CY26SU10`, canvas 1280×720 (`FitToPage`). `pageOrder`: Visão geral → Território → Perfil dos vínculos → Operadoras e mercado (as duas últimas se chamavam Carteiras e vínculos e Financeiro e cobertura). Tema próprio `ANSPanorama` + visuais HTML Content (Secure) e Deneb.

| Página | ID | Visuais |
|---|---|---|
| Visão geral (finalizada) | `b3570a60a7124608b862` | 2× HTML Content (cabeçalho, KPIs), `pageNavigator`, 5× Deneb (série, regiões, capitais × interior, 2 composições) |
| Território (redesenhada) | `71c2a4e6b8d09f3a1c02` | 3× HTML Content (cabeçalho, KPIs, perfil da UF), `pageNavigator`, 2× Deneb (cartograma compacto com seleção, halteres com destaque) |
| Perfil dos vínculos (redesenhada) | `d2b8f6a1c3e45d9f0b12` | 2× HTML Content (cabeçalho, KPIs), `pageNavigator`, 2× Deneb (pirâmide etária, contratação por UF) |
| Operadoras e mercado (redesenhada) | `e3c9a7b2d4f56e0a1c23` | 2× HTML Content (cabeçalho, KPIs), `pageNavigator`, 3× Deneb (ranking de operadoras, concentração, receita por modalidade) |

Filtros de visual obrigatórios (proteção contra dupla contagem): `UF[Tipo]="real"`, `Região[Tipo]="regiao"`, `Recorte de vínculos[Recorte]="modalidade"|"tipo_contratacao"`, `Período[Tipo de granularidade]="trimestral"|"anual"`. Detalhe em `../../CONTEXTO.md` §7.

IDs: páginas em 20 hex; visual = `a` + contador de 19 dígitos hex; filtro = `Filter` + 24 hex.

## 4. Autoria e validação (CLIs)

```powershell
# validar schema do relatório (sempre)
powerbi-report-author.ps1 validate "powerbi\ANS_Panorama\ANS_Panorama.Report"   # 0 erros (aviso de schema 2.14.0 inacessível offline é esperado)

# abrir no Desktop e capturar telas
$env:PBI_DESKTOP_PATH = "C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.159.883.0_x64__8wekyb3d8bbwe\bin\PBIDesktop.exe"
powerbi-desktop.ps1 open "powerbi\ANS_Panorama\ANS_Panorama.pbip"
powerbi-desktop.ps1 screenshot-all "<...>\ANS_Panorama.Report"
```

- `powerbi-report-author.ps1` também expõe `catalog`, `formatting`, `expr`, `theme`, `text`, `preview-visuals/pages/filters/themes`, `preview`, `scaffold`, `pack`/`unpack`.
- `preview --host desktop` não usa dados live; o host `service` exigiria modelo publicado + workspace (GUIDs). Para validar números, conectar o MCP `powerbi-authoring-local` à instância do Desktop (`ListLocalInstances`) e rodar DAX contra valores esperados.

## 5. Convenções e pegadinhas (lições aprendidas)

- **Colisão de nome medida × coluna na mesma tabela** derruba a carga no Desktop (`PFE_XL_MEASURE_COLUMN_ALREADY_EXIST`). Validar **sempre** com um scan por tabela antes de recarregar (o MCP e o `validate` não pegam isso). Ocorreu em `Vínculos por UF e competência` e `Receitas por operadora e ano`; resolvido renomeando as medidas para `Vínculos (sem odontológico exclusivo)` e `Receita de contraprestações (operadora)`.
- **Script gerador de PBIR em PowerShell**: `PS 5.1` lê arquivo `.ps1` **sem BOM** como ANSI → acentuação vira mojibake em todos os nomes do relatório. Gravar o `.ps1` em **UTF-8 com BOM**. O JSON de saída usa `[System.IO.File]::WriteAllText(path, json, New-Object System.Text.UTF8Encoding($false))` (UTF-8 sem BOM).
- **`ConvertTo-Json` (PS 5.1)** precisa de `-Depth` alto; arrays aninhados de **um elemento** em `Values` exigem o operador vírgula unária `,@(...)` (senão o validador acusa `Values/0 must be array`).
- Tipos de visual: usar `cardVisual` (role `Data`), nunca `card`/`multiRowCard` (depreciados); evitar `map`/`filledMap` (→ `azureMap`), `tableEx`/`matrix` e filtros TopN (risco de render).
- Palavras reservadas do PowerShell: não usar `$pid` como variável de loop (é somente leitura).
- **Indentação mista no TMDL (ocorreu em 27/10/2026):** em medida multilinha, linhas só com espaços (`    CALCULATE (...)`, `    formatString:`) fazem o parser tratar `formatString` e `lineageTag` como parte da expressão DAX (erro `SYNTAXERROR`; cards de receita com "Há algo errado em um ou mais campos"). Padrão correto: corpo da expressão com 3 tabs (+ espaços de continuação), propriedades (`formatString`, `lineageTag`) com 2 tabs. Detectar: `INFO.MEASURES()` filtrando `CONTAINSSTRING([Expression], "lineageTag")` (deve devolver 0 linhas).
- **`reload` do CLI não recarrega o modelo semântico** (só o relatório): após editar TMDL com o Desktop aberto, feche o Desktop sem alterações pendentes e reabra (`PBI_DESKTOP_PATH` precisa estar definido para o `open`); depois recarregue os dados.
- **DAX pelo terminal:** carregar `Microsoft.PowerBI.AdomdClient.dll` (pasta `bin` do Desktop; copiar para uma pasta temporária e usar `[Reflection.Assembly]::LoadFrom`) e abrir `AdomdConnection("Data Source=localhost:<porta do msmdsrv>")`. Serve para `EVALUATE ROW(...)`, `INFO.MEASURES()` e validação de números. Nomes com acento exigem aspas simples (`'Região'[Nome]`).
- Caminhos com acento: `read` falha fora da subpasta `tables/`; usar `Get-Content -LiteralPath ... -Encoding UTF8`.

## 6. Estado e próximos passos

Feito em 27/10/2026:

1. Dados carregados; modelo validado por DAX (38 medidas sem erro, totais reconciliando em 53.055.406 — `../../CONTEXTO.md` §6.1).
2. Corrigidos: cards de receita (indentação do TMDL), vínculos somados entre trimestres (regra de estoque), capitais por UF (`UF-capital`) e média de cobertura (ano mais recente).
3. As 4 páginas foram capturadas após as correções.

Defeitos visuais da versão antiga: todos resolvidos com o redesenho das quatro páginas.

Redesenho visual (27/10/2026):

- **Tema próprio** `StaticResources/RegisteredResources/ANSPanorama-7c3e91a2.json` (registrado em `report.json`): fundo `#F4F3EF`, painéis brancos com raio 10 e borda `#E7E5DF`, texto `#16181D`/`#5B6170`/`#8A8F99`, acento `#0E6E6B`, coral `#E0684B` para alerta, Segoe UI/Segoe UI Semibold. Ao editar o tema, trocar o sufixo do nome e as 3 referências em `report.json` (cache do Desktop).
- **Página Visão geral** refeita: cabeçalho + selo "Dados até", faixa de 6 KPIs num `cardVisual` multi-valor (rótulos via `displayName` da projeção), série trimestral, barras ordenadas por região, tipo de contratação e modalidade (o donut virou barras). O slicer de período saiu desta página (retrato mais recente + série histórica).
- **`Operadoras com vínculos` corrigida:** passou a contar só operadoras com vínculos > 0 (662 em Jun/26). O fato traz 758 operadoras em todo trimestre, inclusive linhas zeradas.
- `Variação anual de vínculos` e `Variação anual de receita` passaram a usar `formatString: +0.0%;-0.0%;0.0%` (sinal explícito). Formatar por medida no `cardVisual` com seletor `metadata` + `customFormatString` validou, mas **não** teve efeito no Desktop.
- Visuais personalizados registrados em `report.json` → `publicCustomVisuals`: HTML Content **Secure** `htmlContent443BE3AD55E043BF878BED274D3A6865` (papel de dados `content`; GUID e papéis conferidos em html-content.com/docs/pbir-guide) e Deneb `deneb7E15AEF80B9E4D4F8E12924291ECE89A` (papel `dataset`; especificação em `objects.vega[0].properties.jsonSpec`, configuração em `jsonConfig`, `provider` `vegaLite`; conferido no `capabilities.json` do repositório deneb-viz/deneb).
- **Faixa de KPIs da Visão geral em HTML Content:** medida `KPI HTML - Panorama` (tabela `Vínculos por UF e competência`, pasta `Apresentação`). Monta 4 cards (valor, pílula de variação, contexto e mini-série em SVG inline) só a partir das medidas de negócio; números de geometria serializados com `FORMAT(..., "en-US")` e rótulos com `"pt-BR"`. A edição Secure aceitou SVG inline (`polyline`, `rect`, `circle`) e estilos inline. Testar a expressão antes de gravar: `EVALUATE ROW("h", <expressão>)` via ADOMD.
- **Visão geral, 2ª versão (27/10/2026):** cabeçalho em HTML Content com frase-resumo dinâmica (medida `Cabeçalho HTML - Panorama`); navegador de páginas nativo (`pageNavigator`) no lugar do selo "Dados até"; em Deneb, a série trimestral (área + linha, rótulos no primeiro e no último ponto, anotação de variação calculada na própria especificação), o cartograma das 27 UFs colorido pela cobertura (grade fixa de colunas/linhas na especificação; tooltip com cobertura, vínculos e participação) e as composições de tipo de contratação e modalidade (valor · participação, destaque na maior categoria, categorias abaixo de 0,5% resumidas em nota — não ocultadas).
- Decisões do Deneb: seleção/filtro cruzado **desligado** nesta página (um clique numa UF zeraria as composições, que são de nível Brasil); números formatados com `replace(format(...), '.', ',')` em vez de depender do locale; eixo da série pela `Ordem` numérica (ordenar pelo rótulo em camadas cai em ordem alfabética); área com `stack: null` para o eixo não começar em zero.
- **Território (27/10/2026):** visuais antigos (título, card, slicer de UF, barras de UF, capital × interior e capitais) substituídos. Medidas de apresentação novas: `Cabeçalho HTML - Território` e `KPI HTML - Território` (pasta `Apresentação`). Cartograma em grade compacta (6 × 7, sem vãos internos), halteres de cobertura (primeiro × último ano, ordenado pela cobertura atual, linha tracejada na média simples das UFs) e ranking das 27 UFs (3 maiores em destaque). Sem filtro cruzado (só tooltips). O recorte capital × interior ficou no KPI de capitais; município, só nas próximas iterações (drillthrough).
- **Divisão de papéis (27/10/2026):** o cartograma saiu da Visão geral (repetia a Território). Lá entraram "Onde estão os vínculos" (`composicao.json` com `Região[Nome]` + `Vínculos por grande região`, filtro `Região[Tipo] = "regiao"`) e "Capitais e interior" (barra dividida a partir de `Vínculos capital + interior`, visual `a0000000000000000031`). Na Território, o ranking de UFs deu lugar ao painel `Perfil HTML - UF`, e o mapa ganhou seleção (`enableSelection`; estilo por `__selected__`). Interações em `page.json` → `visualInteractions`: mapa → cabeçalho, navegador e KPIs = `NoFilter`; mapa → halteres = `HighlightFilter` (halteres com `enableHighlight`, opacidade por `cob__highlightStatus`); mapa → perfil = `DataFilter`.
- **Padrão das páginas redesenhadas:** cabeçalho HTML (título, frase-resumo calculada, nota) à esquerda e navegador à direita na faixa superior; 4 KPIs em HTML Content em 1232 × 124; área analítica a partir de y = 246 até y = 700; visuais em painéis brancos do tema, com título + subtítulo do contêiner; números formatados em pt-BR.
- **Perfil dos vínculos (27/10/2026):** página renomeada (era Carteiras e vínculos). Medidas `Cabeçalho HTML - Perfil` e `KPI HTML - Perfil` (cada participação usa o total do próprio recorte). Pirâmide (`piramide.json`): F em valores negativos e M positivos num só eixo; ordem das faixas pelo menor `Ordem` da faixa; pontos invisíveis em ±máx × 1,12 forçam eixo simétrico; faixa "Inconsistente" (87 vínculos) vai para nota. Contratação por UF (`contratacao_uf.json`): 100% empilhado com `stack` manual, categorias pseudo agrupadas em "Outros". O gráfico antigo de faixa × sexo que não mostrava "Até 1 ano" foi substituído.
- **Operadoras e mercado (27/10/2026):** página renomeada (era Financeiro e cobertura). Medidas `Cabeçalho HTML - Mercado`, `KPI HTML - Mercado` (HHI = Σ participação² × 10.000 entre operadoras com vínculos > 0; receita por vínculo = receita do ano ÷ vínculos de dezembro do mesmo ano) e `Vínculos das operadoras - ano anterior`. Specs: `ranking_oper.json` (15 maiores; demais somadas em nota), `concentracao.json` (curva acumulada, eixo log) e `receita_modalidade.json` (anos ≤ `Último ano completo`; 4 maiores coloridas, demais em cinza, rótulos numa coluna à direita para não colidir).
- **Lição do Deneb:** com `autosize: fit`, o Vega-Lite já reserva espaço para rótulos posicionados fora da área do gráfico; somar `padding` extra para eles encolhe o gráfico duas vezes.
- **Lição de Power Query:** ao acrescentar um passo depois do último, colocar vírgula no fim da linha anterior (faltou em `Operadora` e o Desktop abriu "Sem título" com erro de M). Para o portfólio público: trocar `PastaCurated` por parâmetro documentado, publicar capturas no README e só publicar na web com autorização explícita.
