# ANS — Panorama da Saúde Suplementar no Brasil

Projeto de base analítica construída **exclusivamente** a partir do **ANS TabNet** (interface web), sem API, sem FTP
e sem repositório alternativo. A camada analítica (`raw/` → `tidy/` → `curated/`) está validada e é consumida por um
**projeto Power BI** (`powerbi/ANS_Panorama`, formato PBIP): semantic model em TMDL + relatório de 4 páginas.

> **Ponto de entrada para entender e operar o projeto: [`CONTEXTO.md`](CONTEXTO.md).**

**Extraído em:** 16/10/2026 · **Fonte declarada:** `SIB/ANS/MS – 08/2026` (beneficiários e cobertura) e
`ANS – 2º trim/2026, corte 25/08/2026` (receitas) · **29 arquivos originais**, 6 consultas `.def`.

## Estrutura

```
ANS_Saude_Suplementar/
├─ raw/           29 CSVs originais do TabNet (nunca editados) — 1,3 MB
├─ tidy/          29 arquivos em formato longo (dimensao;periodo;valor;medida;…) — 30 MB
├─ curated/       camada analítica: 10 dimensões + 10 fatos + scripts + validações — 14 MB
│  └─ LEIA-ME.md  modelo, chaves, cruzamentos válidos e inválidos, limitações
├─ inventario/    inventário das bases, relatório de qualidade, regras de chave geográfica
├─ powerbi/       ANS_Panorama: semantic model (TMDL) + relatório (PBIR) — 4 páginas
│  └─ ANS_Panorama/LEIA-ME.md  modelo, medidas, páginas, autoria e validação
├─ meta/          log de extração, geradores da camada derivada e validadores
└─ CONTEXTO.md    ponto de entrada único (objetivo, regras, métricas, índice)
```

## Camadas e responsabilidade

| Camada | Papel | Regra |
|---|---|---|
| `raw/` | evidência primária | **imutável**; qualquer alteração invalida as validações |
| `tidy/` | desempilhamento fiel do original (1 célula = 1 linha) | não interpreta geografia nem arredonda |
| `curated/` | modelagem analítica (dimensões, fatos, tipos, chaves) | onde as regras de negócio são aplicadas |
| `powerbi/` | consumo analítico (semantic model + relatório) | consome `curated/`; não altera dados |

## Como reproduzir

```bash
# 1) extração (só se precisar recoletar; grava raw/ e meta/extracao_log.jsonl)
#    driver: meta/extrator_tabnet.py (39 submissões p/ 29 arquivos; roda dentro do browser_exec)
# 2) camada derivada
python meta/gera_tidy.py            # tidy/ (29)
python meta/validar_semantica.py    # 29/29 OK (impede a recorrência do R8)
python meta/gera_inventario.py      # inventario/inventario_bases.{md,csv,json}
python meta/valida_fase1r.py        # 17 validações de reconciliação -> inventario/validacoes_fase1r.*
# 3) camada analítica
python curated/scripts/build_curated.py
python curated/scripts/validar_curated.py   # 16/16 OK -> curated/validacoes_curated.*
# 4) Power BI: abrir powerbi/ANS_Panorama/ANS_Panorama.pbip no Desktop (ver LEIA-ME da pasta)
```

## Números-chave

| Métrica | Valor |
|---|---|
| Arquivos originais | 29 (5.352 a 289.764 bytes) |
| Linhas de dados | 14.268 |
| Células brutas / observações úteis | 187.514 / **180.773** |
| Células vazias | 0 |
| Períodos | 21 competências trimestrais (Jun/2021→Jun/2026) · 6 anos (2021→2026) · snapshot Ago/2026 |
| Tabelas na `curated` | 10 dimensões + 10 fatos |
| Validações | 17 de reconciliação (17/17) + 29 semânticas (29/29) + 16 da camada analítica (16/16) |

## Documentos

- `CONTEXTO.md` — ponto de entrada único (objetivo, regras, métricas, glossário e índice).
- `inventario/inventario_bases.md` (também `.csv`/`.json`) — 29 bases com fonte, URL, eixo, cadência, medida, período, linhas e as duas contagens de células.
- `inventario/relatorio_qualidade.md` — achados R1–R10 com tratamento, validações e 10 limitações (L1–L10).
- `inventario/regras_chaves_geograficas.md` — chave canônica `TIPO:CODIGO`, pseudo-membros e regras de junção.
- `inventario/validacoes_fase1r.csv` — resultado das 17 validações de reconciliação dos originais.
- `curated/LEIA-ME.md` — modelo analítico completo (grãos, aditividade, cruzamentos válidos × inválidos).
- `powerbi/ANS_Panorama/LEIA-ME.md` — semantic model, medidas, páginas do relatório, autoria e validação.
- `meta/extracao_log.jsonl` — log por consulta: data/hora, duração, tentativa, eixos, filtros, URL de export, bytes e SHA-256.

## Aviso de procedência

A coleta original da Fase 1 (14/10/2026) foi perdida (pasta apagada sem backup). Esta é uma **re-extração integral** feita
em 16/10/2026 pelos mesmos 6 formulários, filtros e janela temporal; os 29 arquivos resultaram **byte a byte idênticos**
aos da coleta perdida (bytes e SHA-256 conferidos contra a linha de base guardada), e os 17 testes de reconciliação
reproduziram os mesmos valores. Ou seja: a base da ANS não mudou entre as duas datas e não houve revisão retroativa.
