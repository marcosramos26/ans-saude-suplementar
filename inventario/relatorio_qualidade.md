# Relatório de qualidade dos dados — ANS / Saúde Suplementar

**Projeto:** Panorama da Saúde Suplementar no Brasil (base analítica para Power BI)
**Coleta:** 16/10/2026, pela interface web do **ANS TabNet** (navegador), botão *"Copia como .CSV"* de cada consulta
**Origem declarada pelo TabNet:** `SIB/ANS/MS – 08/2026` (beneficiários e cobertura) · `ANS – 2º trim/2026, corte 25/08/2026` (receitas)
**Consultas:** 6 `.def` distintos, 29 arquivos, 34 submissões (5 falhas recuperadas — log em `meta/extracao_log.jsonl`)

## 1. Procedência desta coleta (Fase 1R)

A pasta da coleta original (14/10/2026) foi apagada sem backup. Esta é uma **re-extração integral** pelos mesmos 6 formulários,
com os mesmos filtros e a mesma janela temporal. Resultado verificado contra a linha de base guardada da Fase 1:

| Verificação | Resultado |
|---|---|
| Arquivos com **bytes e SHA-256 idênticos** aos da Fase 1 | **29/29** |
| Linhas de dados | 14.268 (igual) |
| Observações úteis | 180.773 (igual) |
| Células vazias | 0 (igual) |

Como os 29 arquivos são **byte a byte iguais** aos da Fase 1, todos os achados e conclusões da auditoria técnica daquela
coleta continuam válidos para esta, e não houve revisão retroativa da base entre as duas datas.

## 2. Panorama

| Métrica | Valor |
|---|---|
| Arquivos CSV originais | **29** (+ 29 na camada `tidy`) |
| Linhas de dados (sem as linhas `Total`) | **14.268** |
| Células **brutas** (incluem a coluna `Total` dos 4 arquivos que a têm) | **187.514** |
| **Observações analíticas úteis** (linhas × colunas de período, sem a coluna `Total`) | **180.773** |
| Células vazias / não numéricas | **0** |
| Rótulos duplicados dentro de um arquivo | **0** |
| Períodos | Trimestral **Jun/2021 → Jun/2026** (21 competências) · Anual **2021→2026** · Snapshot **Ago/2026** |

## 3. Estrutura dos arquivos (padrão único do TabNet)

```
Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais   <- linha 1: título da consulta
Assistência Médica por UF e Competência                         <- linha 2: medida + eixos
Período:Jun/2021, Set/2021, ... , Jun/2026                      <- linha 3: período(s) (ou 4ª linha, nos arquivos municipais)
"UF";"Jun/26";"Mar/26";...;"Jun/21"                             <- cabeçalho (colunas = períodos, ordem DECRESCENTE)
"Acre";46916;46770;...;43223                                    <- dados
"Total";53055406;...;48567656                                   <- linha de total (somaria em dobro)
```

- **Encoding:** ISO-8859-1 (latin-1) em 100% dos arquivos · **separador `;`** · todas as células entre aspas · CRLF.
- **3 ou 4 linhas de metadados** antes do cabeçalho · formato **largo** (cada período é uma coluna) → exige *Unpivot*.
- **Números:** inteiros sem separador de milhar; exceção: taxa de cobertura em **percentual com vírgula decimal** (`9,0`).

## 4. Achados e tratamento

| # | Achado | Onde | Tratamento |
|---|---|---|---|
| R1 | **Colisão de rótulo:** `São Paulo`/`Rio de Janeiro` valem como UF **e** capital; 27 rótulos `XX0000 Município ignorado - UF` parecem município e são resíduo | arquivos de UF/município/capital | Regras de chave canônica `TIPO:CODIGO` em `inventario/regras_chaves_geograficas.md`; aplicadas na camada `curated/` |
| R2 | **Linha de município com código de UF inconsistente:** `172208 Wanderlândia` também aparece no arquivo Centro-Oeste, com 7 vínculos em Jun/2026 | `raw/beneficiarios_municipio/*` | O valor pertence ao agregado de **Goiás** (diferença de Goiás == valor da linha em 21/21 competências; Tocantins já fecha sem ela). A linha entra na `curated` como `PSEUDO:GO_municipio_nao_identificado`, com `codigo_origem` preservado e flag — **sem** atribuição a Wanderlândia |
| R3 | Grãos incompatíveis: AM × EO (53.055.406 × 36.736.226 em Jun/26), UF × Região × Município × Capital/Interior, agregado × partes | todos | Fatos separados por grão e regra de não-junção documentada (`curated/LEIA-ME.md`) |
| R4 | 96 operadoras com beneficiários fora do cadastro ativo; 225 ativas sem beneficiários no período | operadora × cadastro | Junção unidirecional com membro "sem correspondência" |
| R5 | `Não Identificado` (UF) e `000000 Ignorado ou exterior` (município) são a mesma massa (46.910 em Jun/26) com rótulos diferentes | UF e município | Mapeamento explícito para `PSEUDO:` na `curated` |
| R6 | 4 municípios da cobertura usam chave `CÓDIGO-Nome` (hífen) em vez de `CÓDIGO Nome` | `taxa_cobertura_municipio` | Extração do código por regex `^(\d{6})[-\s]` |
| R7 | 27 municípios têm beneficiários e não têm taxa; `510183 Boa Esperança Do Norte` tem taxa e não tem beneficiários | beneficiários × cobertura | Junção unidirecional (fato → dimensão) |
| R8 | `periodo`/`medida` trocados na camada derivada das duas bases de cobertura | `tidy/taxa_cobertura_*` | **Corrigido no gerador** (`meta/gera_tidy.py`): o detector de período aceita `Mmm/AA`, `mmm/AAAA` e `AAAA`; `medida` = `Taxa de Cobertura (%)` |
| R9 | `valor` textual (inteiro × decimal com vírgula) e `periodo` com três granularidades na mesma coluna | todos | Tipagem por família na `curated` (`unidade` + `medida_aditiva`) |
| R10 | Células brutas confundidas com observações úteis | inventário e resumos | Inventário passa a registrar as duas contagens: 187.514 × 180.773 |

## 5. Validações executadas

**17 testes de reconciliação** (`meta/valida_fase1r.py` → `inventario/validacoes_fase1r.{json,csv}`) — todos OK:
soma das 28 UFs == linha `Total` · municípios (6 arquivos) == total UF · sexo · grande região · segmentação grupo ·
modalidade · tipo de contratação · faixa etária · Interior · Capital vs linha `Capital` · UF × tipo de contratação (5 arquivos) ·
faixa etária × sexo · operadora == total UF · AM ≠ EO · coluna `Total` da taxa == **média** dos anos (23,97 vs 24,00) ·
coluna `Total` de receitas == **soma** dos anos · cobertura municipal (5.598 rótulos).
Nenhuma validação soma percentuais.

**Bateria semântica raw × tidy** (`meta/validar_semantica.py`) — **29/29 OK**: vocabulário de `periodo` contra as colunas do
original, coerência de `medida` (não pode ser rótulo de período), cardinalidade (linhas × períodos), chave única
`(dimensao, periodo)`, valores preenchidos e classe numérica única por arquivo. É o gate que impede a recorrência do R8.

## 6. Limitações

| ID | Limitação | Impacto | Alternativa |
|---|---|---|---|
| L1 | **TabNet não tem dado mensal** (carga trimestral; o portal remete números mensais à Sala de Situação) | o pedido original de "dados mensais" não é atendível aqui | usar as 21 competências trimestrais; Sala de Situação não oferece exportação tabular |
| L2 | TabNet permite **2 eixos** por tabela | não existe arquivo único com todas as dimensões cruzadas | modelar como **cuboides** (fatos por grão) |
| L3 | A tabela `Município × 21 competências` completa derruba a aba | não é exportável em um arquivo único | fatiada em 6 arquivos por Grande Região (soma validada) |
| L4 | Consulta por **Operadora não oferece Sexo nem Faixa etária** | análise demográfica por operadora é impossível | cruzar `dim_operadora` com os cuboides de UF/sexo/faixa |
| L5 | **Taxa de cobertura é anual** e o período mais recente vem rotulado `Ago/2026` | não alinhar com competência trimestral sem normalizar o ano | usar como série anual independente |
| L6 | **Receitas/Despesas**: extraída 1 das 7 contas (Receita de contraprestações), R$ correntes | sem sinistralidade/margem | reextrair as demais contas (mesmo padrão) |
| L7 | Instabilidade do navegador durante extrações pesadas | nenhuma perda de dado: cada arquivo é verificado no disco e logado | retentativa por lote (ver `meta/extracao_log.jsonl`) |
| L8 | URLs de exportação (`/csv/<sessão>.csv`) são temporárias | não é possível rebaixar pelo mesmo link | refazer a consulta pelos `.def` (documentados no inventário) |
| L9 | **Sem validação externa**: as conferências são internas (partições × total do próprio TabNet) | não prova que o número publicado está correto | confrontar com SIB/ANS ou publicação oficial, se necessário |
| L10 | Duas linhas de cobertura municipal integralmente zeradas | ruído de 2 linhas em 5.571 | manter; filtrar no visual se necessário |
