# Regras de chaves geográficas — evitando colisões entre UF, capital e município

**Escopo:** as 29 bases extraídas do ANS TabNet (Fase 1R, 16/10/2026). Documento de regras, sem alteração de dados.
**Problema que ele resolve:** no TabNet, UF, capital e município vêm todos na coluna `dimensao` (texto), sem prefixo de
tipo. O mesmo texto pode significar entidades diferentes, e há rótulos que *parecem* município (têm 6 dígitos) mas são
resíduos estatísticos, não territórios.

## 1. Colisões verificadas nos dados (evidência)

| Rótulo | Significados encontrados | Ocorrências | Onde |
|---|---|---|---|
| `São Paulo` | **UF** e **capital** | 9 arquivos | `beneficiarios_uf_*` (UF) × `beneficiarios_capital_*` (capital) |
| `Rio de Janeiro` | **UF** e **capital** | 8 arquivos | idem |
| `110000 Município ignorado - RO` … `520000 Município ignorado - GO` | **parece município (tem código), é resíduo por UF** | 27 rótulos (1 por UF) | arquivos `beneficiarios_municipio_*` |
| `000000 Ignorado ou exterior` | parece município, é resíduo nacional | 1 rótulo | `beneficiarios_municipio_competencia_am_exterior_nao_identificado.csv` |
| `Não Identificado` | resíduo em **duas dimensões distintas** (UF e Grande Região) | 7 arquivos | `beneficiarios_uf_*`, `beneficiarios_grande_regiao_*` |
| `Capital` / `Interior` | **partição geográfica**, não território; não soma com as linhas de UF | 2 rótulos | `beneficiarios_interior_competencia_am.csv` |

Consequência prática: os 27 rótulos `XX0000 Município ignorado - UF` explicam por que a lista municipal dos beneficiários
tem 5.597 rótulos distintos contra 5.571 da taxa de cobertura. Eles **não** são municípios: não entram em mapa, em
contagem de municípios nem em junção com a taxa de cobertura.

## 2. Regra central: chave canônica com prefixo de tipo

Nunca unir, agrupar ou comparar tabelas pelo campo `dimensao` cru. Toda dimensão geográfica recebe uma chave `TIPO:CODIGO`:

| Classe | Chave canônica | Como derivar do dado extraído | Situação |
|---|---|---|---|
| UF | `UF:<codigo IBGE 2 dígitos>` | o TabNet exporta **apenas o nome**; a correspondência código↔sigla vem do próprio dado (rótulos `XX0000 Município ignorado - UF`) | validada por reconciliação (ver §3 da modelagem) |
| Município | `MUN:<codigo IBGE 6 dígitos>` | regex `^(\d{6})[-\s]` sobre o rótulo (a taxa usa hífen em 4 casos) | pronta |
| Capital | `CAP:<codigo do município>` | o TabNet exporta **só o nome** (27 capitais, sem código) → de-para nome→código | pronta na camada `curated` |
| Operadora | `OPER:<registro ANS 6 dígitos>` | regex `^(\d{6})-` (as bases de operadora usam `codigo-NOME`) | pronta |
| Pseudo-membro | `PSEUDO:<rotulo>` | ver lista fechada abaixo | pronta |

`UF:São Paulo` e `CAP:São Paulo` são entidades diferentes, mesmo com texto igual. Com prefixo, a colisão deixa de existir.

## 3. Lista fechada de pseudo-membros (não são território)

`000000 Ignorado ou exterior` · `110000`…`520000` `Município ignorado - UF` (27) · `Não Identificado` ·
`Não Informado` · `Coletivo não identificado` · `Capital` · `Interior`

1. **Não descartar** — carregam massa (46.910 vínculos em Jun/2026) e sem eles a soma não fecha.
2. **Não mapear** para município/UF real nem para coordenada geográfica.
3. Em mapa: exibir como "sem localização" ou excluir com aviso de que a soma parcial não é o total.
4. `Capital` + `Interior` **jamais** na mesma soma que as linhas de UF: é partição paralela.

## 4. Regras de junção entre bases

| Regra | Por quê |
|---|---|
| Unir tabelas apenas com o mesmo grão e a mesma medida | grãos diferentes (UF × Município × Operadora) somam em dobro |
| Agregar por chave canônica, nunca por `dimensao` | colisões da §1 |
| Junção unidirecional (fato → dimensão) ao cruzar beneficiários com cobertura | 27 municípios têm beneficiários e não têm taxa; `510183 Boa Esperança Do Norte` só tem taxa |
| Validar o código de 6 dígitos contra o prefixo de UF esperado | a linha `172208 Wanderlândia` dentro do arquivo Centro-Oeste tem código de Tocantins (tratada como provisória na `curated`) |
| Operadora: membro "sem correspondência" explícito | 96 operadoras com beneficiários fora do cadastro ativo; 225 ativas sem beneficiários no período |
| Nunca `INNER JOIN` entre fato e dimensão | descarta linhas em silêncio |

## 5. Testes obrigatórios antes de publicar o modelo

| # | Teste | Critério de aprovação |
|---|---|---|
| T1 | Colisão de chave canônica | nenhuma chave `TIPO:CODIGO` com dois significados |
| T2 | Soma das partes == total | por competência, as partições batem com o total nacional |
| T3 | Métrica repetida | nenhuma medida somada em duas tabelas unidas |
| T4 | Cardinalidade pós-junção | nº de linhas e soma de valor inalterados após cada junção |
| T5 | Pseudo-membros | todos classificados como `PSEUDO:` e visíveis como "sem localização" |

T2 é coberto pelas 17 validações (`meta/valida_fase1r.py`) e pelos testes da camada `curated`
(`curated/scripts/validar_curated.py`); T1, T3, T4 e T5 são implementados na `curated` e no Power Query.
