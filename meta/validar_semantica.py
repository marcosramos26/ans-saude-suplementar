"""Validacoes semanticas das bases derivadas (tidy) contra os CSVs originais (raw).

Regras verificadas por arquivo
  S1  o conjunto de valores de `periodo` deve ser EXATAMENTE o esperado, derivado do raw:
      - colunas com formato de periodo (Jun/26, dez/2021, 2021) -> esses rotulos;
      - se nao houver coluna-periodo, usa-se a linha de metadados "Periodo:".
  S2  `periodo` nao pode ser uma lista concatenada (mais de um periodo no mesmo campo).
  S3  `medida` deve ser constante no arquivo, nao vazia e NAO pode ser um rotulo de periodo
      (evita o defeito em que `periodo` e `medida` ficam trocados - achado R8);
      quando existe coluna-medida nomeada no raw (ex.: Ops._com_Benef.), `medida` deve ser o nome dela.
  S4  o numero de linhas do tidy == linhas de dados x periodos esperados (excluindo a coluna Total).
  S5  (dimensao, periodo) e chave unica; nenhum `valor` vazio; rotulos do raw == dimensoes do tidy.
  S6  todos os valores do arquivo pertencem a uma unica classe numerica
      (inteiro com sinal opcional x decimal com virgula) - impede misturar contagem e taxa.

Uso:
  python meta/validar_semantica.py [--raw DIR] [--tidy DIR] [--quieto]

Codigo de saida: 0 = todas as bases passaram; 1 = pelo menos uma falhou.
"""
import argparse
import csv
import io
import os
import re
import sys

MES = 'jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez'
PER_RE = re.compile(r'^(%s)/\d{2,4}$|^\d{4}$' % MES, re.I)
INT_RE = re.compile(r'^-?\d+$')
DEC_RE = re.compile(r'^-?\d{1,3}(\.\d{3})*,\d+$')


def classe_numerica(s):
    s = s.strip()
    if s == '':
        return 'vazio'
    if INT_RE.match(s):
        return 'inteiro'
    if DEC_RE.match(s):
        return 'decimal_virgula'
    return 'nao_numerico:' + s


def ler_raw(path):
    txt = open(path, 'rb').read().decode('latin-1')
    linhas = [l for l in txt.replace('\r\n', '\n').split('\n') if l != '']
    hdr = next(i for i, l in enumerate(linhas) if l.startswith('"'))
    meta, tab = linhas[:hdr], list(csv.reader(io.StringIO('\n'.join(linhas[hdr:])), delimiter=';'))
    cols, dados = tab[0], tab[1:]
    dims = [r for r in dados if r[0].strip().lower() != 'total']
    per_meta = ''
    for m in meta:
        if m.lower().startswith(('período', 'periodo')):
            per_meta = m.split(':', 1)[1].strip() if ':' in m else ''
    colunas_per = [c.strip() for c in cols[1:] if PER_RE.match(c.strip())]
    colunas_medida = [c.strip() for c in cols[1:]
                      if not PER_RE.match(c.strip()) and c.strip().lower() != 'total']
    esperado = colunas_per if colunas_per else [p.strip() for p in per_meta.split(',') if p.strip()]
    valores = [c for r in dims for j, c in enumerate(r[1:], start=1)
               if cols[j].strip().lower() != 'total']
    return {'cols': cols, 'rotulos': [r[0].strip() for r in dims], 'periodos_esperados': esperado,
            'colunas_medida': colunas_medida, 'linhas_esperadas': len(dims) * len(esperado),
            'classes': sorted({classe_numerica(v) for v in valores})}


def validar(nome, caminho_raw, caminho_tidy):
    falhas = []
    r = ler_raw(caminho_raw)
    with open(caminho_tidy, encoding='utf-8-sig', newline='') as fh:
        linhas = list(csv.DictReader(fh, delimiter=';'))
    esperado = set(r['periodos_esperados'])
    periodos = {l['periodo'] for l in linhas}
    medidas = {l['medida'] for l in linhas}

    if periodos != esperado:
        falhas.append('S1 periodo fora do vocabulario do raw | faltando=%s | inesperado=%s'
                      % (sorted(esperado - periodos)[:3], [s[:40] for s in sorted(periodos - esperado)[:3]]))
    concat = [p for p in periodos if ',' in p or len(p) > 12]
    if concat:
        falhas.append('S2 periodo concatenado (lista em um campo): %s' % [c[:60] for c in concat[:2]])
    if len(medidas) != 1:
        falhas.append('S3 medida nao constante no arquivo: %s' % sorted(medidas)[:4])
    else:
        m = next(iter(medidas))
        if not m.strip():
            falhas.append('S3 medida vazia')
        if PER_RE.match(m.strip()) or m.strip() in esperado:
            falhas.append('S3 medida contem rotulo de periodo (periodo/medida trocados): "%s"' % m[:60])
        if r['colunas_medida'] and m.strip() not in r['colunas_medida']:
            falhas.append('S3 medida "%s" difere da coluna-medida do raw %s' % (m[:40], r['colunas_medida']))
    if len(linhas) != r['linhas_esperadas']:
        falhas.append('S4 linhas do tidy %d != esperado %d' % (len(linhas), r['linhas_esperadas']))
    chaves = [(l['dimensao'], l['periodo']) for l in linhas]
    if len(chaves) != len(set(chaves)):
        falhas.append('S5 chave (dimensao, periodo) duplicada em %d casos' % (len(chaves) - len(set(chaves))))
    vazios = sum(1 for l in linhas if l['valor'].strip() == '')
    if vazios:
        falhas.append('S5 %d valores vazios' % vazios)
    if len(r['classes']) > 1:
        falhas.append('S6 classes numericas misturadas no arquivo: %s' % r['classes'])
    if set(r['rotulos']) != {l['dimensao'] for l in linhas}:
        falhas.append('S5 rotulos do raw != dimensoes do tidy')
    return falhas


def main():
    ap = argparse.ArgumentParser(description='Validacoes semanticas raw x tidy (ANS TabNet).')
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument('--raw', default=os.path.join(raiz, 'raw'))
    ap.add_argument('--tidy', default=os.path.join(raiz, 'tidy'))
    ap.add_argument('--quieto', action='store_true')
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    tidy = sorted(f for f in os.listdir(a.tidy) if f.lower().endswith('.csv'))
    raw_idx = {}
    for dirpath, _, files in os.walk(a.raw):
        for f in files:
            if f.lower().endswith('.csv'):
                raw_idx[f] = os.path.join(dirpath, f)

    print('validacao semantica | tidy=%s' % a.tidy)
    print('bases a validar: %d' % len(tidy))
    print('-' * 100)
    n_falha = 0
    for nome in tidy:
        if nome not in raw_idx:
            print('FALHA %s -> original correspondente nao encontrado em raw/' % nome)
            n_falha += 1
            continue
        falhas = validar(nome, raw_idx[nome], os.path.join(a.tidy, nome))
        if falhas:
            n_falha += 1
        if not a.quieto:
            with open(os.path.join(a.tidy, nome), encoding='utf-8-sig') as fh:
                reg = list(csv.DictReader(fh, delimiter=';'))
            per = len({l['periodo'] for l in reg})
            med = {l['medida'] for l in reg}
            print('%s %-62s periodos=%d medida=%s' % ('OK  ' if not falhas else 'FALHA', nome[:62],
                                                      per, sorted(med)[0][:34] if len(med) == 1 else '?'))
            for f in falhas:
                print('      - ' + f)
    print('-' * 100)
    print('bases validadas: %d | com falha: %d' % (len(tidy), n_falha))
    if n_falha:
        print('RESULTADO: FALHOU - corrija antes de usar a camada tidy.')
        return 1
    print('RESULTADO: OK - camada tidy coerente com os originais (periodo, medida, cardinalidade, unidade).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
