"""Fase 1R - driver de extracao ANS TabNet (29 arquivos) com log, retentativa e verificacao.

Uso dentro do browser_exec:
    exec(open(os.path.join(os.environ['BH_AGENT_WORKSPACE'],'ans2.py')).read())
    run(J[0:4])          # executa um lote por id/indice
"""
import os, json, csv, time, hashlib, datetime

# Raiz do projeto: variável de ambiente ANS_BASE ou, sem ela, a pasta de trabalho atual (o script roda via exec()).
BASE = os.environ.get('ANS_BASE') or os.getcwd()
STAGE = os.path.join(BASE, '_stage')
LOG = os.path.join(BASE, 'meta', 'extracao_log.jsonl')
for d in [STAGE, os.path.join(BASE, 'meta'), os.path.join(BASE, 'raw')]:
    os.makedirs(d, exist_ok=True)

URL = {
 'br': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_br.def',
 '02': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_02.def',
 'cc': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_cc.def',
 'tx': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_tx.def',
 'rc': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_rc.def',
 '03a': 'https://www.ans.gov.br/anstabnet/cgi-bin/dh?dados/tabnet_03a.def',
}

TRIM21 = ['Jun/2021','Set/2021','Dez/2021','Mar/2022','Jun/2022','Set/2022','Dez/2022','Mar/2023',
          'Jun/2023','Set/2023','Dez/2023','Mar/2024','Jun/2024','Set/2024','Dez/2024','Mar/2025',
          'Jun/2025','Set/2025','Dez/2025','Mar/2026','Jun/2026']
TX6 = ['Dez/2021','Dez/2022','Dez/2023','Dez/2024','Dez/2025','Ago/2026']
RC6 = ['2021','2022','2023','2024','2025','2026']
SNAP = ['Ago/2026']

def J(idd, defid, pasta, nome, linha, coluna, inc, per, filtros=None, nota=''):
    return dict(id=idd, defid=defid, pasta=pasta, nome=nome, linha=linha, coluna=coluna,
                inc=inc, per=per, filtros=filtros or {}, nota=nota)

JOBS = [  # ---- grupo 1: Beneficiarios por UF/RM/Capital (tabnet_br) -> 17 arquivos
 J('uf_am','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_assistencia_medica.csv','UF','Competência',['Assistência_Médica'],TRIM21),
 J('uf_eo','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_excl_odontologico.csv','UF','Competência',['Excl._Odontológico'],TRIM21),
 J('regiao','br','beneficiarios_uf_rm_capital','beneficiarios_grande_regiao_competencia_am.csv','Grande_Região','Competência',['Assistência_Médica'],TRIM21),
 J('capital','br','beneficiarios_uf_rm_capital','beneficiarios_capital_competencia_am.csv','Capital','Competência',['Assistência_Médica'],TRIM21),
 J('sexo','br','beneficiarios_uf_rm_capital','beneficiarios_sexo_competencia_am.csv','Sexo','Competência',['Assistência_Médica'],TRIM21),
 J('faixa','br','beneficiarios_uf_rm_capital','beneficiarios_faixa_etaria_competencia_am.csv','Faixa_etária','Competência',['Assistência_Médica'],TRIM21),
 J('tipos','br','beneficiarios_uf_rm_capital','beneficiarios_tipo_contratacao_competencia_am.csv','Tipo_de_contratação','Competência',['Assistência_Médica'],TRIM21),
 J('segment','br','beneficiarios_uf_rm_capital','beneficiarios_segmentacao_grupo_competencia_am.csv','Segmentação_grupo','Competência',['Assistência_Médica'],TRIM21),
 J('modal','br','beneficiarios_uf_rm_capital','beneficiarios_modalidade_competencia_am.csv','Modalidade','Competência',['Assistência_Médica'],TRIM21),
 J('uf_ind','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_tipo_individual_familiar.csv','UF','Competência',['Assistência_Médica'],TRIM21,{'STipo_de_contratação':['1']}),
 J('uf_coemp','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_tipo_coletivo_empresarial.csv','UF','Competência',['Assistência_Médica'],TRIM21,{'STipo_de_contratação':['2']}),
 J('uf_adesao','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_tipo_coletivo_por_adesao.csv','UF','Competência',['Assistência_Médica'],TRIM21,{'STipo_de_contratação':['3']}),
 J('uf_conid','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_tipo_coletivo_nao_identificado.csv','UF','Competência',['Assistência_Médica'],TRIM21,{'STipo_de_contratação':['4']}),
 J('uf_ninf','br','beneficiarios_uf_rm_capital','beneficiarios_uf_competencia_tipo_nao_informado.csv','UF','Competência',['Assistência_Médica'],TRIM21,{'STipo_de_contratação':['5']}),
 J('faixa_m','br','beneficiarios_uf_rm_capital','beneficiarios_faixa_etaria_competencia_sexo_masculino.csv','Faixa_etária','Competência',['Assistência_Médica'],TRIM21,{'SSexo':['1']}),
 J('faixa_f','br','beneficiarios_uf_rm_capital','beneficiarios_faixa_etaria_competencia_sexo_feminino.csv','Faixa_etária','Competência',['Assistência_Médica'],TRIM21,{'SSexo':['2']}),
 J('interior','br','beneficiarios_uf_rm_capital','beneficiarios_interior_competencia_am.csv','Interior','Competência',['Assistência_Médica'],TRIM21),
 # ---- grupo 2: Beneficiarios por Municipio (tabnet_02) -> 6 arquivos fatiados por Grande Regiao
 J('mun_norte','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_norte.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['1']}),
 J('mun_nordeste','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_nordeste.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['2']}),
 J('mun_sudeste','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_sudeste.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['3']}),
 J('mun_sul','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_sul.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['4']}),
 J('mun_coeste','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_centro_oeste.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['5']}),
 J('mun_ext','02','beneficiarios_municipio','beneficiarios_municipio_competencia_am_exterior_nao_identificado.csv','Município','Competência',['Assistência_Médica'],TRIM21,{'SGrande_Região':['6','7']}),
 # ---- grupo 3: Beneficiarios por Operadora (tabnet_cc) -> 1
 J('oper','cc','beneficiarios_operadora','beneficiarios_operadora_competencia_am.csv','Operadora','Competência',['Benef._Asst._Médica'],TRIM21),
 # ---- grupo 4: Taxa de cobertura (tabnet_tx) -> 2
 J('tx_uf','tx','taxa_cobertura','taxa_cobertura_uf_ano_assistencia_medica.csv','UF','Ano',['Assistência_Médica'],TX6),
 J('tx_mun','tx','taxa_cobertura','taxa_cobertura_municipio_ano_assistencia_medica.csv','Município','Ano',['Assistência_Médica'],TX6),
 # ---- grupo 5: Receitas e despesas (tabnet_rc) -> 2
 J('rc_oper','rc','receitas_despesas','receitas_despesas_operadora_ano_contraprestacoes.csv','Operadora','Ano',['Receita_de_contraprestações'],RC6),
 J('rc_modal','rc','receitas_despesas','receitas_despesas_modalidade_ano_contraprestacoes.csv','Modalidade','Ano',['Receita_de_contraprestações'],RC6),
 # ---- grupo 6: Operadoras com registro ativo (tabnet_03a) -> 1
 J('ops_ativas','03a','operadoras_ativas','operadoras_ativas_ago2026.csv','Operadora','--Não-Ativa--',['Ops._com_Benef.'],SNAP),
]

# ---------------------------------------------------------------- helpers de formulario
def _fn_setmulti():
    return '''(() => {
      const out = {};
      window.__alvo = ALVO; window.__vals = VALS;
      for (const [nome, vals] of Object.entries(ALVO)) {
        const s = document.querySelector('select[name="' + nome + '"]');
        if (!s) { out[nome] = 'SELECT_AUSENTE'; continue; }
        let n = 0;
        for (const o of s.options) { o.selected = vals.includes(o.value); if (o.selected) n++; }
        out[nome] = n + '/' + vals.length;
      }
      return JSON.stringify(out);
    })()'''

def aplicar(cfg):
    """aplica eixos, medida, periodos e filtros; devolve o estado lido do formulario"""
    js_alvo = json.dumps({cfg['linha']: 1})  # placeholder, substituido abaixo
    # eixos (selects simples)
    r1 = js('''(() => {
      const set=(nome,val,porTexto)=>{const s=document.querySelector('select[name="'+nome+'"]');
        if(!s) return 'AUSENTE';
        for(const o of s.options){const ok = porTexto ? (o.text.trim()===val) : (o.value===val); o.selected=ok;}
        return s.value;};
      return JSON.stringify({linha:set('Linha',LINHA,false), coluna:set('Coluna',COLUNA,false)});
    })()'''.replace('LINHA', json.dumps(cfg['linha'])).replace('COLUNA', json.dumps(cfg['coluna'])))
    # medida + periodos + filtros (multi)
    alvo = {'Incremento': cfg['inc'], 'Arquivos': cfg['per']}
    alvo.update(cfg['filtros'])
    st = js('''(() => {
      const alvo = ALVO; const out = {};
      for (const nome in alvo) {
        const vals = alvo[nome];
        const s = document.querySelector('select[name="' + nome + '"]');
        if (!s) { out[nome] = 'SELECT_AUSENTE'; continue; }
        let n = 0;
        for (const o of s.options) {
          const ok = vals.includes(o.value) || vals.includes(o.text.trim());
          o.selected = ok; if (ok) n++;
        }
        out[nome] = n + '/' + vals.length;
      }
      return JSON.stringify(out);
    })()'''.replace('ALVO', json.dumps(alvo, ensure_ascii=False)))
    return json.loads(r1), json.loads(st)

def submeter():
    r = js('''(() => {const b=document.querySelector('input[name="mostre"]'); if(!b) return null;
      b.scrollIntoView({block:'center'}); const rc=b.getBoundingClientRect();
      return JSON.stringify({x:rc.x+rc.width/2, y:rc.y+rc.height/2});})()''')
    if not r: return False
    c = json.loads(r); time.sleep(0.4)
    click_at_xy(c['x'], c['y'])
    return True

def esperar_resultado(seg=150):
    """espera a pagina de resultado (link /csv/) e devolve href + cabecalho lido"""
    t0 = time.time()
    while time.time() - t0 < seg:
        try:
            d = js('''(() => {
              const a=[...document.querySelectorAll('a')].find(x=>/Copia como .CSV/i.test(x.innerText) && /\\/csv\\//.test(x.getAttribute('href')||''));
              const txt=(document.body.innerText||'').replace(/\\s+/g,' ');
              const i=txt.indexOf('Período');
              return JSON.stringify({href: a? a.getAttribute('href'):null, url: location.href,
                                     cabecalho: txt.slice(Math.max(0,i-160), i+120)});
            })()''')
            d = json.loads(d)
            if d.get('href'):
                return d
        except Exception as e:
            d = {'erro': str(e)[:80]}
        time.sleep(3)
    return None

def baixar(href, nome_destino, seg=180):
    cdp('Browser.setDownloadBehavior', behavior='allow', downloadPath=STAGE, eventsEnabled=True)
    antes = set(os.listdir(STAGE))
    r = js('''(() => {const a=[...document.querySelectorAll('a')].find(x=>/Copia como .CSV/i.test(x.innerText));
      a.scrollIntoView({block:'center'}); const rc=a.getBoundingClientRect();
      return JSON.stringify({x:rc.x+rc.width/2, y:rc.y+rc.height/2});})()''')
    c = json.loads(r); time.sleep(0.4)
    click_at_xy(c['x'], c['y'])
    t0 = time.time(); arq = None
    while time.time() - t0 < seg:
        novos = [f for f in os.listdir(STAGE) if f not in antes and not f.endswith('.crdownload')]
        if novos:
            p = os.path.join(STAGE, novos[0])
            s1 = os.path.getsize(p); time.sleep(1.2)
            if os.path.getsize(p) == s1 and s1 > 0:
                arq = p; break
        time.sleep(1.5)
    if not arq:
        return None
    destino = os.path.join(BASE, 'raw', nome_destino)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(destino):
        destino = destino.replace('.csv', '_repetido.csv')
    os.replace(arq, destino)
    return destino

def registrar(e):
    with open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(e, ensure_ascii=False) + '\n')

def executar(cfg, max_tent=2):
    t0 = time.time()
    rel = {'id': cfg['id'], 'def': URL[cfg['defid']], 'linha': cfg['linha'], 'coluna': cfg['coluna'],
           'medida': cfg['inc'], 'periodos': len(cfg['per']), 'filtros': cfg['filtros'],
           'inicio': datetime.datetime.now().isoformat(timespec='seconds')}
    for tent in range(1, max_tent + 1):
        rel['tentativa'] = tent
        try:
            if tent == 1:
                # navega so uma vez por arquivo (reaproveita a pagina nas retentativas)
                try:
                    goto_url(URL[cfg['defid']])
                except Exception:
                    new_tab(URL[cfg['defid']])
                wait_for_load(); time.sleep(1.5)
            else:
                goto_url(URL[cfg['defid']]); wait_for_load(); time.sleep(1.5)
            eixos, multi = aplicar(cfg)
            rel['cfg_aplicada'] = {'eixos': eixos, 'multi': multi}
            if 'SELECT_AUSENTE' in json.dumps(multi) or 'AUSENTE' in json.dumps(eixos):
                rel.update(status='erro_form', ok=False)
                registrar({**rel, 'duracao_s': round(time.time() - t0, 1)})
                continue
            if not submeter():
                rel.update(status='erro_sem_botao', ok=False); continue
            time.sleep(2)
            res = esperar_resultado(150)
            if not res:
                rel.update(status='timeout', ok=False)
                registrar({**rel, 'duracao_s': round(time.time() - t0, 1)})
                try: ensure_real_tab()
                except Exception: pass
                continue
            rel['url_export'] = res['href']
            rel['cabecalho'] = res.get('cabecalho', '')[:200]
            cam = baixar(res['href'], os.path.join(cfg['pasta'], cfg['nome']))
            if not cam:
                rel.update(status='falha_download', ok=False)
                registrar({**rel, 'duracao_s': round(time.time() - t0, 1)})
                continue
            b = open(cam, 'rb').read()
            rel.update(status='ok', ok=True, arquivo=cam, bytes=len(b),
                       sha256=hashlib.sha256(b).hexdigest()[:32],
                       linhas=b.decode('latin-1').count('\n') + 1)
            registrar({**rel, 'duracao_s': round(time.time() - t0, 1)})
            return rel
        except Exception as e:
            rel.update(status='excecao:' + str(e)[:60], ok=False)
            registrar({**rel, 'duracao_s': round(time.time() - t0, 1)})
            try: ensure_real_tab()
            except Exception: pass
        time.sleep(2)
    return rel

def run(alvo):
    try:
        ensure_real_tab()          # sempre acorda a aba antes do lote (evita 'no close frame')
    except Exception:
        pass
    ids = [a if isinstance(a, str) else a['id'] for a in alvo]
    out = []
    for j in JOBS:
        if j['id'] in ids:
            r = executar(j)
            out.append({k: r.get(k) for k in ('id','status','ok','bytes','linhas','url_export','cabecalho','tentativa')})
            print('%-9s %-16s ok=%-5s %9s bytes %7s linhas' % (r['id'], str(r.get('status'))[:16],
                  r.get('ok'), r.get('bytes'), r.get('linhas')))
    oks = sum(1 for r in out if r.get('ok'))
    print('--- lote: %d/%d ok ---' % (oks, len(out)))
    return out
