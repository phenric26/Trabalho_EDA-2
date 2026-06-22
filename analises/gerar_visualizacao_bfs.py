"""
Gera um arquivo HTML interativo com:
  - Tabela de distâncias BFS entre todas as regiões
  - Visualizador de caminho BFS entre duas regiões selecionadas
  - Busca por ingrediente (mostra em quais regiões aparece e com qual peso)

Como executar (a partir da raiz do projeto):
    python3 gerar_visualizacao.py

Gera: data/output/visualizacao_bfs.html
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.grafo import graph, region_idx, ing_idx, vertices_region, vertices_ingredient
from bfs import bfs, reconstruir_caminho

# ── rodar BFS a partir de todas as regiões ────────────────────────────────── #

print("Rodando BFS a partir de todas as regiões...")

n_regioes = len(vertices_region)

# bfs_results[região] = (distancias, pais)
bfs_results = {}
for nome_regiao in vertices_region:
    idx = region_idx[nome_regiao]
    dist, pais = bfs(graph, idx)
    bfs_results[nome_regiao] = (dist, pais)

print(f"  {n_regioes} BFS concluídos.")

# ── montar dados para o HTML ──────────────────────────────────────────────── #

def nome_vertice(idx):
    if idx < n_regioes:
        return {"tipo": "regiao", "nome": vertices_region[idx]}
    return {"tipo": "ingrediente", "nome": vertices_ingredient[idx - n_regioes]}

# Tabela de distâncias: distancia_matrix[origem][destino] = int
distancia_matrix = {}
for origem in vertices_region:
    dist, _ = bfs_results[origem]
    distancia_matrix[origem] = {}
    for destino in vertices_region:
        idx_destino = region_idx[destino]
        distancia_matrix[origem][destino] = dist.get(idx_destino, -1)

# Caminhos: caminhos[origem][destino] = [{"tipo": ..., "nome": ...}, ...]
print("Reconstruindo caminhos entre todas as regiões...")
caminhos = {}
for origem in vertices_region:
    _, pais = bfs_results[origem]
    caminhos[origem] = {}
    for destino in vertices_region:
        idx_destino = region_idx[destino]
        caminho_idx = reconstruir_caminho(pais, idx_destino)
        caminhos[origem][destino] = [nome_vertice(v) for v in caminho_idx]

# Ingredientes por região (para busca): ingredientes_por_regiao[regiao] = [{nome, peso}]
print("Montando índice de ingredientes por região...")
ingredientes_por_regiao = {}
for nome_regiao in vertices_region:
    idx_r = region_idx[nome_regiao]
    vizinhos = graph.get(idx_r, [])
    lista = []
    for viz_idx, peso in sorted(vizinhos, key=lambda x: -x[1]):
        nome_ing = vertices_ingredient[viz_idx - n_regioes]
        lista.append({"nome": nome_ing, "peso": round(peso, 4)})
    ingredientes_por_regiao[nome_regiao] = lista

# Regiões por ingrediente (para busca inversa): regioes_por_ingrediente[ing] = [{regiao, peso}]
regioes_por_ingrediente = {}
for nome_ing, idx_i in ing_idx.items():
    vizinhos = graph.get(idx_i, [])
    lista = []
    for viz_idx, peso in sorted(vizinhos, key=lambda x: -x[1]):
        nome_r = vertices_region[viz_idx]
        lista.append({"regiao": nome_r, "peso": round(peso, 4)})
    regioes_por_ingrediente[nome_ing] = lista

# ── serializar para JSON embutido no HTML ─────────────────────────────────── #

dados_js = {
    "regioes": vertices_region,
    "distancias": distancia_matrix,
    "caminhos": caminhos,
    "ingredientes_por_regiao": ingredientes_por_regiao,
    "regioes_por_ingrediente": regioes_por_ingrediente,
    "todos_ingredientes": sorted(ing_idx.keys()),
}

json_str = json.dumps(dados_js, ensure_ascii=False)

# ── template HTML ─────────────────────────────────────────────────────────── #

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análise BFS — Grafo Culinário</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: #2e3250;
    --accent: #6c8eff;
    --accent2: #a78bfa;
    --text: #e2e8f0;
    --text-dim: #7c849e;
    --region-color: #6c8eff;
    --ing-color: #34d399;
    --dist0: #1e3a2f;
    --dist2: #1a2a4a;
    --distN: #2a1f1f;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.6;
  }}
  header {{
    padding: 24px 32px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 16px;
  }}
  header h1 {{ font-size: 1.3rem; font-weight: 600; color: var(--accent); }}
  header span {{ color: var(--text-dim); font-size: 0.85rem; }}

  .tabs {{
    display: flex;
    gap: 4px;
    padding: 16px 32px 0;
    border-bottom: 1px solid var(--border);
  }}
  .tab {{
    padding: 8px 20px;
    border-radius: 8px 8px 0 0;
    cursor: pointer;
    color: var(--text-dim);
    border: 1px solid transparent;
    border-bottom: none;
    background: transparent;
    font-size: 0.9rem;
    transition: all 0.15s;
  }}
  .tab:hover {{ color: var(--text); background: var(--surface2); }}
  .tab.active {{
    background: var(--surface);
    color: var(--accent);
    border-color: var(--border);
  }}

  .panel {{ display: none; padding: 24px 32px; }}
  .panel.active {{ display: block; }}

  /* ── Painel 1: Caminho BFS ── */
  .path-controls {{
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 24px;
  }}
  select, input[type=text] {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
    min-width: 200px;
  }}
  select:focus, input:focus {{
    outline: none;
    border-color: var(--accent);
  }}
  .arrow {{ color: var(--accent2); font-size: 1.2rem; }}

  .path-result {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    min-height: 100px;
  }}
  .path-viz {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }}
  .node {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }}
  .node-box {{
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.85rem;
    text-align: center;
    max-width: 160px;
    word-break: break-word;
  }}
  .node-box.regiao {{
    background: #1a2a4a;
    border: 1px solid var(--region-color);
    color: var(--region-color);
  }}
  .node-box.ingrediente {{
    background: #0f2a20;
    border: 1px solid var(--ing-color);
    color: var(--ing-color);
  }}
  .node-label {{
    font-size: 0.7rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .edge-line {{
    color: var(--text-dim);
    font-size: 1.4rem;
    margin: 0 4px;
  }}
  .path-meta {{
    margin-top: 16px;
    color: var(--text-dim);
    font-size: 0.85rem;
    display: flex;
    gap: 24px;
  }}
  .path-meta span {{ color: var(--text); }}

  /* ── Painel 2: Tabela de distâncias ── */
  .table-wrapper {{
    overflow: auto;
    max-height: 70vh;
    border: 1px solid var(--border);
    border-radius: 12px;
  }}
  table {{
    border-collapse: collapse;
    width: max-content;
  }}
  th, td {{
    padding: 8px 12px;
    text-align: center;
    border: 1px solid var(--border);
    font-size: 0.8rem;
    white-space: nowrap;
  }}
  thead th {{
    background: var(--surface2);
    color: var(--accent);
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 2;
  }}
  thead th:first-child {{
    position: sticky;
    left: 0;
    z-index: 3;
  }}
  tbody td:first-child {{
    background: var(--surface2);
    color: var(--accent);
    font-weight: 600;
    position: sticky;
    left: 0;
    z-index: 1;
    text-align: left;
  }}
  td.d0 {{ background: var(--dist0); color: #34d399; font-weight: 700; }}
  td.d2 {{ background: var(--dist2); color: #93c5fd; }}
  td.dN {{ background: var(--distN); color: #f87171; }}
  tbody tr:hover td {{ filter: brightness(1.3); }}
  tbody tr:hover td:first-child {{ filter: brightness(1.1); }}

  /* ── Painel 3: Busca por ingrediente ── */
  .search-wrapper {{ position: relative; max-width: 400px; margin-bottom: 20px; }}
  .search-wrapper input {{ width: 100%; padding-right: 36px; }}
  #autocomplete {{
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 8px 8px;
    max-height: 220px;
    overflow-y: auto;
    z-index: 10;
    display: none;
  }}
  #autocomplete div {{
    padding: 8px 12px;
    cursor: pointer;
    font-size: 0.85rem;
  }}
  #autocomplete div:hover {{ background: var(--surface); color: var(--accent); }}

  .ing-result {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }}
  .ing-result h3 {{ color: var(--ing-color); margin-bottom: 12px; }}
  .regiao-cards {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 8px;
  }}
  .regiao-card {{
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    min-width: 160px;
    cursor: pointer;
    transition: border-color 0.15s;
  }}
  .regiao-card:hover {{ border-color: var(--accent); }}
  .regiao-card .r-nome {{ color: var(--region-color); font-weight: 600; font-size: 0.85rem; }}
  .regiao-card .r-peso {{ color: var(--text-dim); font-size: 0.75rem; margin-top: 2px; }}
  .empty {{ color: var(--text-dim); font-style: italic; }}

  .badge {{
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-left: 8px;
  }}
</style>
</head>
<body>

<header>
  <h1>🍽 Grafo Culinário — Análise BFS</h1>
  <span>{n_regioes} regiões · {len(vertices_ingredient)} ingredientes · {len(ing_idx)} arestas únicas</span>
</header>

<div class="tabs">
  <button class="tab active" onclick="showTab('caminho')">Caminho BFS</button>
  <button class="tab" onclick="showTab('tabela')">Tabela de Distâncias</button>
  <button class="tab" onclick="showTab('ingrediente')">Busca por Ingrediente</button>
</div>

<!-- ── PAINEL 1: Caminho BFS ── -->
<div id="tab-caminho" class="panel active">
  <div class="path-controls">
    <div>
      <div style="color:var(--text-dim);font-size:0.75rem;margin-bottom:4px;">Origem</div>
      <select id="sel-origem" onchange="atualizarCaminho()"></select>
    </div>
    <div class="arrow" style="margin-top:18px;">→</div>
    <div>
      <div style="color:var(--text-dim);font-size:0.75rem;margin-bottom:4px;">Destino</div>
      <select id="sel-destino" onchange="atualizarCaminho()"></select>
    </div>
  </div>

  <div class="path-result" id="path-result">
    <div class="empty">Selecione origem e destino acima.</div>
  </div>
</div>

<!-- ── PAINEL 2: Tabela de distâncias ── -->
<div id="tab-tabela" class="panel">
  <p style="color:var(--text-dim);margin-bottom:16px;font-size:0.85rem;">
    Distância em número de arestas entre cada par de regiões.
    <span style="color:#34d399">■</span> dist=0 &nbsp;
    <span style="color:#93c5fd">■</span> dist=2 &nbsp;
    Clique numa célula para ver o caminho.
  </p>
  <div class="table-wrapper">
    <table id="tabela-dist"></table>
  </div>
</div>

<!-- ── PAINEL 3: Busca por ingrediente ── -->
<div id="tab-ingrediente" class="panel">
  <div class="search-wrapper">
    <input type="text" id="busca-ing" placeholder="Digite um ingrediente..." oninput="autocomplete(this.value)" autocomplete="off">
    <div id="autocomplete"></div>
  </div>
  <div id="ing-result" class="ing-result">
    <div class="empty">Digite um ingrediente para ver em quais regiões ele aparece.</div>
  </div>
</div>

<script>
const DADOS = {json_str};

// ── Inicialização ─────────────────────────────────────────────────────────── //

function init() {{
  const regioes = DADOS.regioes;

  // Popula selects
  ['sel-origem','sel-destino'].forEach(id => {{
    const sel = document.getElementById(id);
    regioes.forEach(r => {{
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = r.charAt(0).toUpperCase() + r.slice(1);
      sel.appendChild(opt);
    }});
  }});
  document.getElementById('sel-destino').value = regioes[1] || regioes[0];

  construirTabela();
  atualizarCaminho();
}}

// ── Tabs ──────────────────────────────────────────────────────────────────── //

function showTab(nome) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + nome).classList.add('active');
  event.target.classList.add('active');
}}

// ── Painel 1: Caminho BFS ─────────────────────────────────────────────────── //

function atualizarCaminho() {{
  const origem  = document.getElementById('sel-origem').value;
  const destino = document.getElementById('sel-destino').value;
  const caminho = DADOS.caminhos[origem][destino];
  const dist    = DADOS.distancias[origem][destino];
  const el      = document.getElementById('path-result');

  if (!caminho || caminho.length === 0) {{
    el.innerHTML = '<div class="empty">Caminho não encontrado.</div>';
    return;
  }}

  let html = '<div class="path-viz">';
  caminho.forEach((no, i) => {{
    const cls = no.tipo === 'regiao' ? 'regiao' : 'ingrediente';
    const label = no.tipo === 'regiao' ? 'Região' : 'Ingrediente';
    html += `
      <div class="node">
        <div class="node-box ${{cls}}">${{no.nome}}</div>
        <div class="node-label">${{label}}</div>
      </div>`;
    if (i < caminho.length - 1) html += '<div class="edge-line">—</div>';
  }});
  html += '</div>';

  // Ingrediente ponte (sempre o nó do meio num grafo bipartido)
  let ponteInfo = '';
  if (caminho.length === 3 && caminho[1].tipo === 'ingrediente') {{
    const ing = caminho[1].nome;
    const pesoOrigem  = (DADOS.ingredientes_por_regiao[origem]  || []).find(x => x.nome === ing);
    const pesoDestino = (DADOS.ingredientes_por_regiao[destino] || []).find(x => x.nome === ing);
    ponteInfo = `
      <div style="margin-top:16px;padding:12px;background:var(--surface2);border-radius:8px;font-size:0.82rem;">
        <span style="color:var(--ing-color);font-weight:600">${{ing}}</span> é o ingrediente ponte
        <span style="color:var(--text-dim);margin-left:8px;">
          TF-IDF em ${{origem}}: <span style="color:var(--text)">${{pesoOrigem ? pesoOrigem.peso.toFixed(4) : '—'}}</span>
          &nbsp;·&nbsp;
          TF-IDF em ${{destino}}: <span style="color:var(--text)">${{pesoDestino ? pesoDestino.peso.toFixed(4) : '—'}}</span>
        </span>
      </div>`;
  }}

  el.innerHTML = html + ponteInfo + `
    <div class="path-meta">
      <div>Distância: <span>${{dist}} aresta(s)</span></div>
      <div>Nós no caminho: <span>${{caminho.length}}</span></div>
    </div>`;
}}

// ── Painel 2: Tabela de distâncias ───────────────────────────────────────── //

function construirTabela() {{
  const regioes = DADOS.regioes;
  const tabela  = document.getElementById('tabela-dist');

  let html = '<thead><tr><th>↓ origem \\ destino →</th>';
  regioes.forEach(r => html += `<th>${{r}}</th>`);
  html += '</tr></thead><tbody>';

  regioes.forEach(orig => {{
    html += `<tr><td>${{orig}}</td>`;
    regioes.forEach(dest => {{
      const d   = DADOS.distancias[orig][dest];
      const cls = d === 0 ? 'd0' : d === 2 ? 'd2' : d === -1 ? 'dN' : '';
      const txt = d === -1 ? '∞' : d;
      html += `<td class="${{cls}}" onclick="irParaCaminho('${{orig}}','${{dest}}')" style="cursor:pointer" title="${{orig}} → ${{dest}}: ${{txt}} aresta(s)">${{txt}}</td>`;
    }});
    html += '</tr>';
  }});

  html += '</tbody>';
  tabela.innerHTML = html;
}}

function irParaCaminho(origem, destino) {{
  document.getElementById('sel-origem').value  = origem;
  document.getElementById('sel-destino').value = destino;
  showTab('caminho');
  // atualiza a tab ativa visualmente
  document.querySelectorAll('.tab').forEach((t,i) => {{
    t.classList.toggle('active', i === 0);
  }});
  atualizarCaminho();
}}

// ── Painel 3: Busca por ingrediente ──────────────────────────────────────── //

function autocomplete(query) {{
  const box = document.getElementById('autocomplete');
  if (query.length < 2) {{ box.style.display = 'none'; return; }}

  const matches = DADOS.todos_ingredientes
    .filter(i => i.includes(query.toLowerCase()))
    .slice(0, 12);

  if (matches.length === 0) {{ box.style.display = 'none'; return; }}

  box.innerHTML = matches.map(m =>
    `<div onclick="selecionarIngrediente('${{m.replace(/'/g,"\\'")}}')">` +
    m.replace(query.toLowerCase(), `<strong>${{query.toLowerCase()}}</strong>`) +
    `</div>`
  ).join('');
  box.style.display = 'block';
}}

function selecionarIngrediente(nome) {{
  document.getElementById('busca-ing').value = nome;
  document.getElementById('autocomplete').style.display = 'none';
  mostrarIngrediente(nome);
}}

function mostrarIngrediente(nome) {{
  const regioes = DADOS.regioes_por_ingrediente[nome];
  const el      = document.getElementById('ing-result');

  if (!regioes || regioes.length === 0) {{
    el.innerHTML = `<div class="empty">"${{nome}}" não encontrado no grafo.</div>`;
    return;
  }}

  let cards = regioes.map(r => `
    <div class="regiao-card" onclick="irParaCaminho('${{r.regiao}}','${{r.regiao}}')">
      <div class="r-nome">${{r.regiao}}</div>
      <div class="r-peso">TF-IDF: ${{r.peso.toFixed(4)}}</div>
    </div>`).join('');

  el.innerHTML = `
    <h3>${{nome}} <span class="badge">${{regioes.length}} regiões</span></h3>
    <p style="color:var(--text-dim);font-size:0.82rem;margin-bottom:12px;">
      Ordenado por relevância (TF-IDF) decrescente. Clique numa região para ver caminhos.
    </p>
    <div class="regiao-cards">${{cards}}</div>`;
}}

// Fecha autocomplete ao clicar fora
document.addEventListener('click', e => {{
  if (!e.target.closest('.search-wrapper'))
    document.getElementById('autocomplete').style.display = 'none';
}});

init();
</script>
</body>
</html>"""

# ── salvar ────────────────────────────────────────────────────────────────── #

output_dir  = os.path.join(os.path.dirname(__file__), "data", "output")
output_path = os.path.join(output_dir, "visualizacao_bfs.html")
os.makedirs(output_dir, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nHTML gerado em: {output_path}")
print("Abra no browser: Ctrl+clique no caminho acima, ou:")
print(f"  xdg-open {output_path}")
