# Inventário das bases extraídas — ANS / Saúde Suplementar

Fonte: **ANS TabNet** (interface web), consultas executadas pelo navegador em **16/10/2026** (Fase 1R).
Todas as tabelas foram exportadas pelo botão **"Copia como .CSV"** de cada consulta.

**Semântica das colunas de contagem** (achado R10):
- `células brutas` = linhas de dados × **todas** as colunas de valor do original, **incluindo** a coluna `Total` quando existe.
- `observações úteis` = linhas de dados × colunas de valor **sem** a coluna `Total` — é exatamente o que a camada `tidy` contém.

| # | Arquivo | Consulta | Eixo | Cadência | Medida | Períodos | Mais antigo | Mais recente | Linhas | Células brutas | Observações úteis | Vazias |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `beneficiarios_municipio_competencia_am_centro_oeste.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 471 | 9891 | 9891 | 0 |
| 2 | `beneficiarios_municipio_competencia_am_exterior_nao_identificado.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 1 | 21 | 21 | 0 |
| 3 | `beneficiarios_municipio_competencia_am_nordeste.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 1803 | 37863 | 37863 | 0 |
| 4 | `beneficiarios_municipio_competencia_am_norte.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 457 | 9597 | 9597 | 0 |
| 5 | `beneficiarios_municipio_competencia_am_sudeste.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 1672 | 35112 | 35112 | 0 |
| 6 | `beneficiarios_municipio_competencia_am_sul.csv` | Beneficiários por Município | Município | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 1194 | 25074 | 25074 | 0 |
| 7 | `beneficiarios_operadora_competencia_am.csv` | Beneficiários por Operadora | Operadora | trimestral | Benef. Asst. Médica | 21 | Jun/21 | Jun/26 | 758 | 15918 | 15918 | 0 |
| 8 | `beneficiarios_capital_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Capital | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 27 | 567 | 567 | 0 |
| 9 | `beneficiarios_faixa_etaria_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Faixa etária | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 19 | 399 | 399 | 0 |
| 10 | `beneficiarios_faixa_etaria_competencia_sexo_feminino.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Faixa etária | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 19 | 399 | 399 | 0 |
| 11 | `beneficiarios_faixa_etaria_competencia_sexo_masculino.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Faixa etária | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 19 | 399 | 399 | 0 |
| 12 | `beneficiarios_grande_regiao_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Grande Região | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 6 | 126 | 126 | 0 |
| 13 | `beneficiarios_interior_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Interior | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 2 | 42 | 42 | 0 |
| 14 | `beneficiarios_modalidade_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Modalidade | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 5 | 105 | 105 | 0 |
| 15 | `beneficiarios_segmentacao_grupo_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Segmentação grupo | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 5 | 105 | 105 | 0 |
| 16 | `beneficiarios_sexo_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Sexo | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 2 | 42 | 42 | 0 |
| 17 | `beneficiarios_tipo_contratacao_competencia_am.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | Tipo de contratação | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 5 | 105 | 105 | 0 |
| 18 | `beneficiarios_uf_competencia_assistencia_medica.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 19 | `beneficiarios_uf_competencia_excl_odontologico.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Excl. Odontológico | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 20 | `beneficiarios_uf_competencia_tipo_coletivo_empresarial.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 21 | `beneficiarios_uf_competencia_tipo_coletivo_nao_identificado.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 7 | 147 | 147 | 0 |
| 22 | `beneficiarios_uf_competencia_tipo_coletivo_por_adesao.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 23 | `beneficiarios_uf_competencia_tipo_individual_familiar.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 24 | `beneficiarios_uf_competencia_tipo_nao_informado.csv` | Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais | UF | trimestral | Assistência Médica | 21 | Jun/21 | Jun/26 | 28 | 588 | 588 | 0 |
| 25 | `operadoras_ativas_ago2026.csv` | Operadoras com registro ativo | Operadora | snapshot mensal | Ops. com Benef. | 0 | Ago/2026 | Ago/2026 | 887 | 887 | 887 | 0 |
| 26 | `receitas_despesas_modalidade_ano_contraprestacoes.csv` | Receitas e Despesas | Modalidade | anual | Receita de contraprestações | 6 | 2026 | 2021 | 8 | 56 | 48 | 0 |
| 27 | `receitas_despesas_operadora_ano_contraprestacoes.csv` | Receitas e Despesas | Operadora | anual | Receita de contraprestações | 6 | 2026 | 2021 | 1135 | 7945 | 6810 | 0 |
| 28 | `taxa_cobertura_municipio_ano_assistencia_medica.csv` | Taxa de Cobertura de Planos de Saúde | Município | anual | Taxa de Cobertura (%) | 6 | ago/2026 | dez/2021 | 5571 | 38997 | 33426 | 0 |
| 29 | `taxa_cobertura_uf_ano_assistencia_medica.csv` | Taxa de Cobertura de Planos de Saúde | UF | anual | Taxa de Cobertura (%) | 6 | ago/2026 | dez/2021 | 27 | 189 | 162 | 0 |

**URLs das consultas (uma por grupo de arquivos):**

- `beneficiarios_uf_rm_capital` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_br.def (trimestral, fonte SIB/ANS/MS)
- `beneficiarios_municipio` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_02.def (trimestral, fonte SIB/ANS/MS)
- `beneficiarios_operadora` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_cc.def (trimestral, fonte SIB/ANS/MS)
- `taxa_cobertura` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_tx.def (anual, fonte SIB/ANS/MS + IBGE)
- `operadoras_ativas` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_03a.def (snapshot mensal, fonte ANS)
- `receitas_despesas` → https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_rc.def (anual, fonte ANS)

**Totais:** 29 arquivos · 14268 linhas de dados · 187514 células brutas · **180773 observações úteis** · 0 vazias