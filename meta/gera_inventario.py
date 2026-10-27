"""Fase 1R - inventario das 29 bases (md, csv, json) com a distincao do achado R10:
   `celulas_brutas`      = linhas de dados x TODAS as colunas de valor (inclui a coluna "Total" quando existe)
   `observacoes_uteis`   = linhas de dados x colunas de valor SEM a coluna "Total"  (= linhas da camada tidy)
Uso: python meta/gera_inventario.py
"""
import csv
import io
import json
import os
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'raw')
INV = os.path.join(BASE, 'inventario')
import sys
sys.path.insert(0, os.path.join(BASE, 'meta'))
from gera_tidy import CONS, MEDIDA_OVERRIDE, carregar, PER_RE  # mesma convencao de medida/periodo


def main():
    os.makedirs(INV, exist_ok=True)
    itens = []
    for rel in sorted(glob.glob(os.path.join(RAW, '*', '*.csv'))):
        grupo = os.path.basename(os.path.dirname(rel))
        consulta, url, cadencia, fonte = CONS[grupo]
        meta, cols, dims = carregar(rel)
        linha_medida = meta[1] if len(meta) > 1 else ''
        medida = MEDIDA_OVERRIDE.get(grupo) or (linha_medida.split(' por ')[0].strip()
                                                if ' por ' in linha_medida else linha_medida.strip())
        per_meta = next((m.split(':', 1)[1].strip() for m in meta
                         if m.lower().startswith(('período', 'periodo'))), '')
        colunas_per = [c.strip() for c in cols[1:] if PER_RE.match(c.strip())]
        colunas_med = [c.strip() for c in cols[1:]
                       if not PER_RE.match(c.strip()) and c.strip().lower() != 'total']
        tem_total = any(c.strip().lower() == 'total' for c in cols[1:])
        uteis_col = len([c for c in cols[1:] if c.strip().lower() != 'total'])
        vazias = sum(1 for r in dims for j, c in enumerate(r[1:], start=1)
                     if cols[j].strip().lower() != 'total' and c.strip() == '')
        rotulos = [r[0].strip() for r in dims]
        itens.append({
            'grupo': grupo, 'nome': os.path.basename(rel), 'consulta': consulta, 'url': url,
            'cadencia': cadencia, 'fonte': fonte, 'medida': medida, 'eixo': cols[0],
            'eixos_meta': linha_medida, 'periodos_colunas': len(colunas_per),
            'colunas_extra': colunas_med,
            'periodo_min': (colunas_per[-1] if colunas_per else per_meta),
            'periodo_max': (colunas_per[0] if colunas_per else per_meta),
            'periodos_meta': per_meta,
            'linhas': len(dims), 'celulas_brutas': len(dims) * (len(cols) - 1),
            'observacoes_uteis': len(dims) * len(colunas_per) if colunas_per else len(dims) * len(colunas_med),
            'vazias': vazias, 'rotulos_dup': sorted({r for r in rotulos if rotulos.count(r) > 1}),
            'col_total': tem_total, 'bytes': os.path.getsize(rel)})
    json.dump(itens, open(os.path.join(INV, 'inventario_bases.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(INV, 'inventario_bases.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['#', 'arquivo', 'consulta', 'URL', 'eixo (linha)', 'cadencia', 'medida',
                    'periodos (colunas)', 'periodo mais antigo', 'periodo mais recente',
                    'linhas de dados', 'celulas brutas', 'observacoes uteis', 'celulas vazias',
                    'rotulos duplicados', 'coluna Total no arquivo', 'bytes', 'fonte'])
        for i, it in enumerate(itens, 1):
            w.writerow([i, it['nome'], it['consulta'], it['url'], it['eixo'], it['cadencia'],
                        it['medida'], it['periodos_colunas'], it['periodo_min'], it['periodo_max'],
                        it['linhas'], it['celulas_brutas'], it['observacoes_uteis'], it['vazias'],
                        len(it['rotulos_dup']), 'sim' if it['col_total'] else 'nao', it['bytes'],
                        it['fonte']])
    L = ['# Inventário das bases extraídas — ANS / Saúde Suplementar', '',
         'Fonte: **ANS TabNet** (interface web), consultas executadas pelo navegador em **16/10/2026** (Fase 1R).',
         'Todas as tabelas foram exportadas pelo botão **"Copia como .CSV"** de cada consulta.', '',
         '**Semântica das colunas de contagem** (achado R10):',
         '- `células brutas` = linhas de dados × **todas** as colunas de valor do original, **incluindo** a coluna `Total` quando existe.',
         '- `observações úteis` = linhas de dados × colunas de valor **sem** a coluna `Total` — é exatamente o que a camada `tidy` contém.', '',
         '| # | Arquivo | Consulta | Eixo | Cadência | Medida | Períodos | Mais antigo | Mais recente | Linhas | Células brutas | Observações úteis | Vazias |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for i, it in enumerate(itens, 1):
        L.append('| %d | `%s` | %s | %s | %s | %s | %d | %s | %s | %d | %d | %d | %d |' % (
            i, it['nome'], it['consulta'], it['eixo'], it['cadencia'], it['medida'],
            it['periodos_colunas'], it['periodo_min'], it['periodo_max'], it['linhas'],
            it['celulas_brutas'], it['observacoes_uteis'], it['vazias']))
    L += ['', '**URLs das consultas (uma por grupo de arquivos):**', '']
    for g, (c, u, cad, f) in CONS.items():
        L.append('- `%s` → %s (%s, fonte %s)' % (g, u, cad, f))
    L += ['', '**Totais:** %d arquivos · %d linhas de dados · %d células brutas · **%d observações úteis** · %d vazias'
          % (len(itens), sum(i['linhas'] for i in itens), sum(i['celulas_brutas'] for i in itens),
             sum(i['observacoes_uteis'] for i in itens), sum(i['vazias'] for i in itens))]
    open(os.path.join(INV, 'inventario_bases.md'), 'w', encoding='utf-8').write('\n'.join(L))
    print('inventario: %d arquivos | linhas %d | celulas brutas %d | observacoes uteis %d | vazias %d'
          % (len(itens), sum(i['linhas'] for i in itens), sum(i['celulas_brutas'] for i in itens),
             sum(i['observacoes_uteis'] for i in itens), sum(i['vazias'] for i in itens)))


if __name__ == '__main__':
    main()
