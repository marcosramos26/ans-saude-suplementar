# Camada `curated/` — modelo analítico (ANS / Saúde Suplementar no Brasil)

Camada analítica derivada de `raw/` (29 originais, intocados) e `tidy/`, pronta para Power BI.
**Não contém dashboard.** Gerada por script, reproduzível, com 16 testes de validação (16/16 OK).

## Como regenerar

```bash
cd ANS_Saude_Suplementar
python curated/scripts/build_curated.py     # dimensões + fatos
python curated/scripts/validar_curated.py   # 16 testes -> curated/validacoes_curated.{json,csv}
```

Pré-requisitos: `tidy/` gerado por `meta/gera_tidy.py` e `raw/` com os 29 CSVs (`meta/extracao_log.jsonl` registra a extração).
Validade dos originais: `python meta/validar_semantica.py` (29/29) e `python meta/valida_fase1r.py` (17/17).

## Estrutura

```
curated/
├─ dims/   dim_periodo · dim_uf · dim_regiao · dim_municipio · dim_capital ·
│          dim_operadora · dim_modalidade · dim_recorte_membro · dim_particao · dim_medida
├─ fatos/  10 tabelas fato (ver abaixo)
├─ scripts/ lib_ans.py · build_curated.py · validar_curated.py
├─ validacoes_curated.csv/.json
└─ LEIA-ME.md (este arquivo)
```

**Convenções:** CSV UTF-8 com BOM, separador `;`, **decimal com ponto**, sem separador de milhar, vazio = nulo.
Números em `vinculos` são inteiros; R$ e percentuais são decimais. Nenhuma coluna `Total` entrou na camada.

## Dimensões

| Dimensão | Grão | Chave | Observação |
|---|---|---|---|
| `dim_periodo` | 34 períodos | `periodo_id` | 21 trimestrais (`T2026Q2`), 6 anuais com mês (`A2021-12`, da cobertura), 6 anuais sem mês (`A2024`, das receitas), 1 snapshot (`S2026-08`). `data_referencia` só é preenchida quando o rótulo traz mês |
| `dim_uf` | 28 | `UF:<2 dígitos>` | 27 UFs + `UF:00` (resíduo nacional). Código↔nome derivado **por reconciliação de valores** (26 UFs com 21/21 competências exatas; Goiás 20/21 por causa do R2) |
| `dim_regiao` | 6 | `REG:<nn>` | 5 regiões + `Não Identificado` |
| `dim_municipio` | 5.599 | `MUN:<6 dígitos>` / `PSEUDO:…` | 5.571 municípios com código (5.570 do IBGE + `510183 Boa Esperança Do Norte`, que só existe na cobertura) + 26 `ignorado_uf` (o DF não tem rótulo ignorado) + `ignorado_exterior` + o membro provisório do R2 |
| `dim_capital` | 27 | `CAP:<nn>` | nome da capital → `municipio_id`; 22 por nome único, 5 (Belém, Boa Vista, Campo Grande, Palmas, Rio Branco) resolvidas por **igualdade da série de valores** entre os homônimos |
| `dim_operadora` | 1.201 | `OPER:<6 dígitos>` | união de 3 fontes (cadastro ativo Ago/2026, fato de beneficiários, fato de receitas) + membro `PSEUDO:sem_correspondencia`; coluna `fontes` diz em quais aparece |
| `dim_modalidade` | 9 | `MODAL:<nome>` | união da modalidade dos beneficiários e das receitas |
| `dim_recorte_membro` | 80 | `(recorte, membro_id)` | membros de sexo, faixa etária, tipo de contratação, segmentação grupo, modalidade, grande região e faixa×sexo (`faixa\|sexo`) |
| `dim_particao` | 2 | `PART:capital` / `PART:interior` | partição paralela, não soma com as linhas de UF |
| `dim_medida` | 11 | `medida_id` | **catálogo de aditividade**: para cada coluna de medida, unidade, tipo, se é aditiva, em que grão pode ser somada e com o que não pode ser combinada |

## Fatos

| Fato | Grão | Medidas | Linhas | Aditiva? |
|---|---|---|---|---|
| `fato_beneficiarios_uf_competencia` | UF × competência | `vinculos_assistencia_medica`, `vinculos_excl_odontologico` | 588 | sim (cada uma) |
| `fato_beneficiarios_recorte_competencia` | nível (`BRASIL`/`UF`/`REGIAO`) × geo × recorte × membro × competência | `vinculos` | 4.179 | sim, **dentro do mesmo recorte/nível/geo** |
| `fato_beneficiarios_particao_competencia` | partição × competência | `vinculos` | 42 | sim |
| `fato_beneficiarios_capital_competencia` | capital × competência | `vinculos` | 567 | sim |
| `fato_beneficiarios_municipio_competencia` | município × competência | `vinculos` | 117.558 | sim |
| `fato_beneficiarios_operadora_competencia` | operadora × competência | `vinculos` | 15.918 | sim |
| `fato_taxa_cobertura_uf_ano` | UF × ano | `taxa_cobertura_pct` | 162 | **não** |
| `fato_taxa_cobertura_municipio_ano` | município × ano | `taxa_cobertura_pct` | 33.426 | **não** |
| `fato_receitas_operadora_ano` | operadora × ano | `receita_contraprestacoes_reais` | 6.810 | sim |
| `fato_receitas_modalidade_ano` | modalidade × ano | `receita_contraprestacoes_reais` | 48 | sim |

## Tratamento dos riscos da auditoria

| Risco | Como ficou na camada |
|---|---|
| **R1** colisão UF × capital × município | chave canônica `TIPO:CODIGO` em todas as tabelas; `dim_municipio` tem a coluna `colide_com_nome_de_uf` marcando os 2 casos; capital e UF são dimensões separadas (`UF:São Paulo` ≠ `CAP:21`) |
| **R2** linha `172208 Wanderlândia` no arquivo Centro-Oeste | entra como `PSEUDO:GO_municipio_nao_identificado`, `uf_id = UF:52`, `codigo_origem = 172208`, `flag_codigo_inconsistente = 1`, `classificacao_provisoria = 1`. **Nenhum vínculo atribuído a Wanderlândia** e nenhum perdido |
| **R3** grãos incompatíveis | fatos separados por grão; `dim_medida` declara, por coluna, o que não pode ser somado junto |
| **R4** operadoras fora de par | união das 3 fontes; 636 nas três, 17 só no cadastro ativo, 22 só nos beneficiários, 217 só nas receitas; membro `PSEUDO:sem_correspondencia` para chave ausente |
| **R5** `Não Identificado` × `000000 Ignorado ou exterior` | ambos em `PSEUDO:` (`UF:00` no eixo UF; `PSEUDO:ignorado_exterior` no eixo município), preservando a massa (46.910 vínculos em Jun/26 no eixo UF; no eixo município o resíduo total é 49.715: 46.910 + 2.798 ignorado na UF + 7 provisório) |
| **R6** chaves com hífen na cobertura | código extraído por `^(\d{6})[-\s]` — os 4 casos (`150475`, `421265`, `422000`, `431454`) entram como `MUN:` normal |
| **R7** escopos diferentes | junção sempre fato → dimensão; 27 municípios sem taxa e `MUN:510183 Boa Esperança Do Norte` sem beneficiários continuam nas dimensões |
| **R9** tipagem e períodos | tipo por família (inteiro/decimal/%); três granularidades separadas em `dim_periodo.tipo_granularidade`, sem inventar periodicidade |
| **R10** células brutas × observações úteis | camada construída a partir das **180.773** observações úteis; nenhuma coluna `Total` entrou (teste V6c) |

## Cruzamentos analiticamente VÁLIDOS

- **UF × competência** com qualquer recorte de **nível UF** (tipo de contratação), por `(periodo_id, uf_id)` — inclusive o total de `fato_beneficiarios_uf_competencia` para calcular participação.
- **UF × competência** com taxa de cobertura **por ano**, por `uf_id` + ano (grãos temporais diferentes: comparar, nunca somar junto).
- **Município × competência** com taxa de cobertura **municipal por ano**, por `municipio_id` + ano.
- **Município → UF**: `fato_beneficiarios_municipio_competencia.uf_id` permite rolar município para UF **na mesma medida**.
- **Capital × competência** com `dim_municipio` (via `dim_capital.municipio_id`) para levar a capital ao mapa.
- **Operadora × competência** com `dim_operadora` (perfil do cadastro, presença nas fontes) e com **receita por operadora/ano** por `operadora_id` (comparar vínculo × receita exige alinhar ano × competência — ver inválidos).
- **Recortes nacionais**: comparar sexo, faixa etária, tipo de contratação, segmentação grupo, modalidade e faixa×sexo **entre si** dentro da mesma competência (todos somam o mesmo total).
- **Receita por modalidade × ano** com **receita por operadora × ano**: só para conferência/participação, nunca somando as duas.

## Cruzamentos INVÁLIDOS (não fazer)

| Combinação | Por quê |
|---|---|
| Somar `vinculos_assistencia_medica` + `vinculos_excl_odontologico` | medidas distintas, não partição |
| Somar `fato_beneficiarios_uf_competencia` + qualquer outro fato | grãos diferentes (UF, município, operadora, capital) — dupla contagem |
| Somar membros de **recortes diferentes** (ex.: "Masculino" + "10 a 14 anos") | recortes se sobrepõem (mesma massa em cortes distintos) |
| Somar `Capital` + `Interior` com as linhas de **UF** | eixos paralelos |
| Somar as **27 capitais** esperando o total nacional | capitais são subconjunto (20,3 mi de 53,0 mi em Jun/26) |
| Somar `taxa_cobertura_pct` (UF ou município) | percentual |
| Somar as duas tabelas de receita (operadora + modalidade) | mesma massa, grãos diferentes |
| Somar receita de **2026** com os anos fechados como se fosse ano completo | 2026 é parcial (corte 25/08/2026) |
| Cruzar vínculo (trimestral) com receita (anual) somando | grãos temporais distintos; alinhar época antes |
| Usar `membro`/`dimensao` textual como chave de junção | colisões documentadas (R1) — usar `*_id` |
| Tratar `PSEUDO:` como território em mapa | não são municípios/UF reais |

## Validações (16/16 OK)

`curated/validacoes_curated.csv`: V1 unicidade de chave em 19 tabelas · V2 integridade referencial (0 chaves órfãs) ·
T4 cardinalidade pós-junção (nenhuma dimensão com chave repetida) · V3a–V3f reconciliação das medidas aditivas
(tipo de contratação por UF, recortes nacionais, municípios, partição Capital+Interior, operadoras, grande região —
todas == total nacional por competência) · V4 cobertura de relacionamento (27/27 capitais; operadoras por fonte) ·
V5a taxas ≥ 0 (1 caso acima de 100%, documentado) · V5b teste **não aditivo** (taxa da UF dentro do min/max municipal do estado) ·
V6a SHA-256 dos 29 originais == log de extração · V6b soma tidy == soma curated · V6c nenhuma coluna `Total`.

## Limitações que permanecem

1. **Sem dado mensal** no TabNet (L1) — a série de vínculos é trimestral.
2. **Identidade do município goiano** do R2 segue indeterminada: o membro provisório preserva o valor (7 em Jun/2026) e a UF (Goiás); resolver exige nova consulta filtrada por Goiás.
3. **Sigla do DF ausente** em `dim_uf` (a fonte não traz rótulo `530000 Município ignorado - DF`); o resto do código↔nome está derivado e validado.
4. **Taxas podem exceder 100%** (1 município, dez/2021) — é razão beneficiários/população, não erro de carga.
5. **Receitas: 1 das 7 contas** (Receita de contraprestações), R$ correntes, sem deflacionamento.
6. **Sem validação externa**: todas as conferências são internas contra o próprio total do TabNet.
