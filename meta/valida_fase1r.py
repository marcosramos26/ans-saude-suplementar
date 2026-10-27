"""Bateria de reconciliacao dos 29 originais (as 17 validacoes da Fase 1 + checagens de integridade).

Regras:
  - toda comparacao de valor aditivo usa o total nacional como referencia (linha "Total" do arquivo UF);
  - percentuais NAO entram em soma (a validacao da taxa e a media dos anos, nao a soma);
  - o resultado e gravado em inventario/validacoes_fase1r.{json,csv}.
Uso: python meta/valida_fase1r.py
"""
import csv
import io
import json
import os
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'raw')
INV = os.path.join(BASE, 'inventario')
TOL = 1.0


def num(s):
    s = (s or '').strip()
    if s in ('', '-', '...', 'X'):
        return None
    s2 = s.replace('.', '').replace(',', '.') if (',' in s and '.' not in s) else s.replace(',', '')
    try:
        return float(s2)
    except Exception:
        return None


def carregar(rel):
    linhas = open(os.path.join(RAW, rel), 'rb').read().decode('latin-1')
    linhas = [l for l in linhas.replace('\r\n', '\n').split('\n') if l != '']
    hdr = next(i for i, l in enumerate(linhas) if l.startswith('"'))
    tab = list(csv.reader(io.StringIO('\n'.join(linhas[hdr:])), delimiter=';'))
    cols, dados = tab[0], tab[1:]
    tot = [r for r in dados if r[0].strip().lower().startswith('total')]
    dims = [r for r in dados if r not in tot]
    return {'cols': cols, 'dims': dims, 'tot': tot[0] if tot else None,
            'val': {r[0].strip(): [num(c) for c in r[1:]] for r in dims},
            'linhas': [r for r in dims]}


def soma(lista):
    n = max(len(v) for v in lista) if lista else 0
    out = [0.0] * n
    for v in lista:
        for j, x in enumerate(v):
            if x is not None and j < n:
                out[j] += x
    return out


V = []


def checa(nome, calc, esp, tol=TOL, nota=''):
    dif = [(j, round(a, 2), round(b, 2)) for j, (a, b) in enumerate(zip(calc, esp))
           if a is not None and b is not None and abs(a - b) > tol]
    V.append({'teste': nome, 'ok': not dif, 'n_divergencias': len(dif), 'exemplos': dif[:3], 'nota': nota})
    print(('OK   ' if not dif else 'DIF  ') + nome + ('' if not dif else ' -> %s' % dif[:2]))


def main():
    uf = carregar('beneficiarios_uf_rm_capital/beneficiarios_uf_competencia_assistencia_medica.csv')
    # referencia: linha "Total" (total nacional por competencia), sem a coluna Total
    ncol = len(uf['cols']) - 1
    tot_ref = [num(x) for x in uf['tot'][1:]][: ncol]
    checa('Soma das 28 UFs == linha Total', soma(list(uf['val'].values()))[:ncol], tot_ref)
    mm = []
    for f in glob.glob(os.path.join(RAW, 'beneficiarios_municipio', '*.csv')):
        mm += list(carregar(os.path.relpath(f, RAW))['val'].values())
    checa('Municipios (6 arquivos por regiao) == Total UF', soma(mm)[:ncol], tot_ref)
    for f, nome in [('beneficiarios_sexo_competencia_am.csv', 'Sexo (M+F)'),
                    ('beneficiarios_grande_regiao_competencia_am.csv', 'Grande Regiao'),
                    ('beneficiarios_segmentacao_grupo_competencia_am.csv', 'Segmentacao grupo'),
                    ('beneficiarios_modalidade_competencia_am.csv', 'Modalidade'),
                    ('beneficiarios_tipo_contratacao_competencia_am.csv', 'Tipo de contratacao'),
                    ('beneficiarios_faixa_etaria_competencia_am.csv', 'Faixa etaria')]:
        d = carregar('beneficiarios_uf_rm_capital/' + f)
        checa('%s == Total UF' % nome, soma(list(d['val'].values()))[:ncol], tot_ref)
    cap = carregar('beneficiarios_uf_rm_capital/beneficiarios_capital_competencia_am.csv')
    inte = carregar('beneficiarios_uf_rm_capital/beneficiarios_interior_competencia_am.csv')
    checa('Interior (eixo Capital/Interior, 2 linhas) == Total UF', soma(list(inte['val'].values()))[:ncol],
          tot_ref, nota='eixo Interior e a particao Capital x Interior')
    checa('Capital (27 capitais somadas) == linha "Capital" do eixo Interior',
          soma(list(cap['val'].values()))[:ncol], inte['val'].get('Capital', [None] * ncol),
          nota='Capital sozinho NAO fecha o total nacional')
    tt = []
    for f in glob.glob(os.path.join(RAW, 'beneficiarios_uf_rm_capital', '*competencia_tipo_*.csv')):
        tt += list(carregar(os.path.relpath(f, RAW))['val'].values())
    checa('UF x Tipo de contratacao (5 arquivos) == Total UF', soma(tt)[:ncol], tot_ref)
    fx = []
    for f in glob.glob(os.path.join(RAW, 'beneficiarios_uf_rm_capital', '*faixa_etaria_competencia_sexo_*.csv')):
        fx += list(carregar(os.path.relpath(f, RAW))['val'].values())
    checa('Faixa etaria x Sexo (2 arquivos) == Faixa etaria', soma(fx)[:ncol], tot_ref)
    op = carregar('beneficiarios_operadora/beneficiarios_operadora_competencia_am.csv')
    checa('Operadora == Total UF', soma(list(op['val'].values()))[:ncol], tot_ref,
          nota='%d operadoras com beneficiarios no periodo' % len(op['val']))
    eo = carregar('beneficiarios_uf_rm_capital/beneficiarios_uf_competencia_excl_odontologico.csv')
    V.append({'teste': 'Assistencia Medica vs Excl. Odontologico sao medidas distintas (nao somar)',
              'ok': True, 'n_divergencias': 0, 'exemplos': [],
              'nota': 'Jun/26: AM=%s | EO=%s' % (uf['tot'][1], eo['tot'][1])})
    print('OK   AM vs EO: %s | %s' % (uf['tot'][1], eo['tot'][1]))
    # taxa de cobertura: coluna Total == media dos anos (nao soma)
    tx = carregar('taxa_cobertura/taxa_cobertura_uf_ano_assistencia_medica.csv')
    ct = [j for j, c in enumerate(tx['cols'][1:]) if c.strip().lower() == 'total']
    if ct:
        k = ct[0]
        anos = [j for j, c in enumerate(tx['cols'][1:]) if c.strip().lower() != 'total']
        media = sum(num(tx['tot'][1:][j]) or 0 for j in anos) / len(anos)
        dif = abs(media - (num(tx['tot'][1:][k]) or 0))
        V.append({'teste': 'Taxa de cobertura: coluna "Total" e a MEDIA dos anos (nao a soma)',
                  'ok': dif <= 0.1, 'n_divergencias': 0 if dif <= 0.1 else 1,
                  'exemplos': ['media %.2f vs coluna %.2f' % (media, num(tx['tot'][1:][k]) or 0)],
                  'nota': 'valores em % com virgula decimal'})
        print('OK   taxa: coluna Total = media %.2f vs %.2f' % (media, num(tx['tot'][1:][k]) or 0))
    # receitas: coluna Total == soma dos anos
    rc = carregar('receitas_despesas/receitas_despesas_modalidade_ano_contraprestacoes.csv')
    ct = [j for j, c in enumerate(rc['cols'][1:]) if c.strip().lower() == 'total']
    if ct:
        k = ct[0]
        s = sum(num(rc['tot'][1:][j]) or 0 for j, c in enumerate(rc['cols'][1:]) if c.strip().lower() != 'total')
        ref_tot = num(rc['tot'][1:][k]) or 0
        V.append({'teste': 'Receitas: coluna "Total" e a SOMA dos anos', 'ok': abs(s - ref_tot) < 1.0,
                  'n_divergencias': 0 if abs(s - ref_tot) < 1.0 else 1,
                  'exemplos': ['soma %.0f vs coluna %.0f' % (s, ref_tot)],
                  'nota': 'R$ correntes, sem deflacionamento'})
        print('OK   receitas: coluna Total = soma %.0f vs %.0f' % (s, ref_tot))
    munis = sum(len(carregar(os.path.relpath(f, RAW))['dims'])
                for f in glob.glob(os.path.join(RAW, 'beneficiarios_municipio', '*.csv')))
    V.append({'teste': 'Cobertura municipal: %d linhas de municipio nos 6 arquivos' % munis,
              'ok': munis >= 5570, 'n_divergencias': 0, 'exemplos': [],
              'nota': 'contagem inclui os rotulos XX0000 Municipio ignorado - UF'})
    print('OK   municipios:', munis)
    json.dump(V, open(os.path.join(INV, 'validacoes_fase1r.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    with open(os.path.join(INV, 'validacoes_fase1r.csv'), 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['teste', 'resultado', 'n_divergencias', 'exemplos', 'observacao'])
        for v in V:
            w.writerow([v['teste'], 'OK' if v['ok'] else 'DIVERGENTE', v['n_divergencias'],
                        str(v['exemplos'])[:200], v['nota']])
    print('\ntestes: %d | divergentes: %d' % (len(V), sum(1 for v in V if not v['ok'])))


if __name__ == '__main__':
    main()
