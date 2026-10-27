"""Fase 1R - gera a camada tidy (wide -> long) a partir dos 29 CSVs originais.

Campos de saida (identicos a Fase 1): dimensao;periodo;valor;medida;consulta;cadencia;granularidade;arquivo_origem

Correcoes embutidas (achado R8 da auditoria):
  - o detector de periodo aceita os tres formatos do TabNet: Mmm/AA (Jun/26), mmm/AAAA (dez/2021) e AAAA (2021);
  - quando a coluna de valor e nomeada (nao e periodo), `medida` recebe o NOME DA COLUNA (ex.: Ops._com_Benef.)
    e `periodo` vem da linha de metadados "Periodo:";
  - a taxa de cobertura tem `medida` explicitamente rotulada como taxa (o valor e percentual, nao contagem).
Uso:  python meta/gera_tidy.py
"""
import csv
import io
import os
import re
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, 'raw')
TIDY = os.path.join(BASE, 'tidy')

PER_RE = re.compile(r'^(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)/\d{2,4}$|^\d{4}$', re.I)

CONS = {
 'beneficiarios_uf_rm_capital': ('Beneficiários por UFs, Regiões Metropolitanas (RM) e Capitais',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_br.def', 'trimestral', 'SIB/ANS/MS'),
 'beneficiarios_municipio': ('Beneficiários por Município',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_02.def', 'trimestral', 'SIB/ANS/MS'),
 'beneficiarios_operadora': ('Beneficiários por Operadora',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_cc.def', 'trimestral', 'SIB/ANS/MS'),
 'taxa_cobertura': ('Taxa de Cobertura de Planos de Saúde',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_tx.def', 'anual', 'SIB/ANS/MS + IBGE'),
 'operadoras_ativas': ('Operadoras com registro ativo',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_03a.def', 'snapshot mensal', 'ANS'),
 'receitas_despesas': ('Receitas e Despesas',
   'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_rc.def', 'anual', 'ANS'),
}
MEDIDA_OVERRIDE = {'taxa_cobertura': 'Taxa de Cobertura (%)'}


def carregar(path):
    texto = open(path, 'rb').read().decode('latin-1')
    linhas = [l for l in texto.replace('\r\n', '\n').split('\n') if l != '']
    hdr = next(i for i, l in enumerate(linhas) if l.startswith('"'))
    meta = linhas[:hdr]
    tab = list(csv.reader(io.StringIO('\n'.join(linhas[hdr:])), delimiter=';'))
    cols, dados = tab[0], tab[1:]
    dims = [r for r in dados if r[0].strip().lower() != 'total']
    return meta, cols, dims


def escrever(info, destino):
    with open(destino, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['dimensao', 'periodo', 'valor', 'medida', 'consulta', 'cadencia',
                    'granularidade', 'arquivo_origem'])
        for r in info['dims']:
            for j, col in enumerate(info['cols'][1:], start=1):
                if col.strip().lower() == 'total':
                    continue
                if PER_RE.match(col.strip()):
                    periodo, medida = col.strip(), info['medida']
                else:
                    periodo, medida = info['per_meta'], col.strip()   # coluna nomeada = medida
                w.writerow([r[0].strip(), periodo, r[j], medida, info['consulta'],
                            info['cadencia'], '%s x %s' % (info['cols'][0], info['cadencia']),
                            os.path.basename(info['arquivo'])])


def main():
    os.makedirs(TIDY, exist_ok=True)
    itens = []
    for rel in sorted(glob.glob(os.path.join(RAW, '*', '*.csv'))):
        grupo = os.path.basename(os.path.dirname(rel))
        consulta, url, cadencia, fonte = CONS[grupo]
        meta, cols, dims = carregar(rel)
        linha_medida = meta[1] if len(meta) > 1 else ''
        medida = MEDIDA_OVERRIDE.get(grupo) or (linha_medida.split(' por ')[0].strip() if ' por ' in linha_medida
                                                else linha_medida.strip())
        per_meta = next((m.split(':', 1)[1].strip() for m in meta
                         if m.lower().startswith(('período', 'periodo'))), '')
        info = {'arquivo': rel, 'cols': cols, 'dims': dims, 'consulta': consulta, 'url': url,
                'cadencia': cadencia, 'fonte': fonte, 'medida': medida, 'per_meta': per_meta}
        escrever(info, os.path.join(TIDY, os.path.basename(rel)))
        itens.append(info)
    print('tidy gerado: %d arquivos' % len(itens))
    return itens


if __name__ == '__main__':
    main()
