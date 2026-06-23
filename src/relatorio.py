"""Orquestrador da análise — gera o relatório final em data/output/relatorio.md.

Não reimplementa nenhum algoritmo: importa as FUNÇÕES de cada peça do grupo
(grafo, fila/bfs, clique, similaridade/Jaccard, cosseno) e a renderização de
figuras (figuras.py), executa tudo para os PESOS escolhidos e emite:

  - data/output/relatorio.md        (a análise final, com as figuras embutidas)
  - data/output/resultados.json     (números crus, reprodutíveis)

É chamado pelo entrypoint fino main.py (que lê os pesos via flags de linha de
comando). Pode rodar direto também: `uv run python3 src/relatorio.py`.
"""

import io
import json
import os
import re
import sys
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

sys.path.insert(0, str(BASE_DIR))  # para importar os scripts de desenho da raiz

_lixo = io.StringIO()
with redirect_stdout(_lixo):
    import similaridade as sim
    import cosseno
    from grafo import vertices_region, vertices_ingredient, region_idx, ing_idx, graph
    from clique import encontrar_cliques_maximos
    from fila.bfs import bfs, reconstruir_caminho
    # scripts de desenho do projeto (só renderizam; reaproveitados como estão)
    import visualizacao as vis
    import visualizacao_similaridade as vis_sim

ID_PARA_NOME = {v: k for k, v in region_idx.items()}
ID_PARA_NOME.update({v: k for k, v in ing_idx.items()})
N_REGIOES = len(vertices_region)
OUT_DIR = BASE_DIR / "data" / "output"

# defaults (também repetidos no main.py para a ajuda do CLI)
LIMIAR_JACCARD = 0.20
PERCENTIL_COSSENO = 0.10
TOP_K = 30
DEFAULT_REGIOES = ["france", "italy", "japan", "china", "mexico"]


# ----------------------------------------------------------------------------
# helpers de grafo / clique
# ----------------------------------------------------------------------------
def _arestas(g):
    e = set()
    for i, vizinhos in g.items():
        for j, _ in vizinhos:
            e.add((i, j) if i < j else (j, i))
    return e


def _grafo_jaccard(limiar, top_k):
    """Grafo região-região por Jaccard, delegando a similaridade.py (agora
    parametrizado por top_k) — fonte única da lógica de Jaccard."""
    return sim.grafo_similaridade(limiar, top_k)


def _grafo_cosseno(percentil):
    with redirect_stdout(_lixo):
        return cosseno.construir_grafo_projetado(region_idx, graph, percentil_top=percentil)


def _familias(g, tam_min=2):
    cliques = encontrar_cliques_maximos(g)
    out = [frozenset(vertices_region[i] for i in c) for c in cliques if len(c) >= tam_min]
    return sorted(out, key=len, reverse=True)


# ----------------------------------------------------------------------------
# seções (cada uma devolve um fragmento do dicionário de resultados)
# ----------------------------------------------------------------------------
def _secao_panorama():
    graus = {r: len(graph.get(r, [])) for r in range(N_REGIOES)}
    n_arestas = sum(graus.values())
    densidade = n_arestas / (N_REGIOES * len(vertices_ingredient))

    exclusivos = []
    for r in range(N_REGIOES):
        for viz, peso in graph.get(r, []):
            exclusivos.append((round(peso, 4), ID_PARA_NOME[r], ID_PARA_NOME[viz]))
    exclusivos.sort(reverse=True)

    graus_ing = {idx: len(graph.get(idx, [])) for idx in ing_idx.values()}
    transversais = sorted(graus_ing.items(), key=lambda kv: -kv[1])[:10]

    g_reg = sorted(graus.values())
    return {
        "n_regioes": N_REGIOES,
        "n_ingredientes": len(vertices_ingredient),
        "n_arestas": n_arestas,
        "densidade_bipartida": round(densidade, 4),
        "grau_regiao_min": g_reg[0],
        "grau_regiao_max": g_reg[-1],
        "grau_regiao_medio": round(sum(g_reg) / len(g_reg), 1),
        "top_exclusivos": [{"regiao": reg, "ingrediente": ing, "tfidf": p}
                           for p, reg, ing in exclusivos[:10]],
        "top_transversais": [{"ingrediente": ID_PARA_NOME[i], "regioes": d}
                             for i, d in transversais],
    }


def _secao_assinaturas(top_n=8):
    out = {}
    for r in range(N_REGIOES):
        viz = sorted(graph.get(r, []), key=lambda x: -x[1])[:top_n]
        out[ID_PARA_NOME[r]] = [{"ingrediente": ID_PARA_NOME[i], "tfidf": round(p, 4)}
                                for i, p in viz]
    return out


def _secao_conectividade():
    distancias, _ = bfs(graph, 0)
    total_vertices = N_REGIOES + len(vertices_ingredient)

    todas = []
    for r in range(N_REGIOES):
        d, _ = bfs(graph, r)
        todas += [d[o] for o in range(N_REGIOES) if o != r and o in d]

    pares_ex = [("japan", "mexico"), ("italy", "japan"),
                ("indian subcontinent", "france"), ("scandinavia", "thailand")]
    exemplos = []
    for a, b in pares_ex:
        if a in region_idx and b in region_idx:
            dist, pais = bfs(graph, region_idx[a])
            if region_idx[b] in dist:
                caminho = reconstruir_caminho(pais, region_idx[b])
                pontes = [ID_PARA_NOME[v] for v in caminho[1:-1]]
                exemplos.append({"de": a, "para": b,
                                 "distancia": dist[region_idx[b]], "ponte": pontes})

    return {
        "grafo_conexo": len(distancias) == total_vertices,
        "vertices_alcancados_de_0": len(distancias),
        "vertices_totais": total_vertices,
        "diametro_regiao_regiao": max(todas) if todas else None,
        "exemplos_ponte": exemplos,
    }


def _secao_familias_regioes(limiar_jaccard, percentil_cosseno, top_k):
    g_jac = _grafo_jaccard(limiar_jaccard, top_k)
    g_cos, limiar_cos, _ = _grafo_cosseno(percentil_cosseno)
    e_jac, e_cos = _arestas(g_jac), _arestas(g_cos)
    cl_jac, cl_cos = _familias(g_jac), _familias(g_cos)

    ambos = e_jac & e_cos
    uniao = e_jac | e_cos
    pares_totais = N_REGIOES * (N_REGIOES - 1) // 2
    nenhum = pares_totais - len(uniao)
    asia = frozenset({"china", "korea", "south east asia", "thailand"})

    return {
        "arestas_jaccard": len(e_jac),
        "arestas_cosseno": len(e_cos),
        "limiar_cosseno_calculado": round(limiar_cos, 4),
        "familias_jaccard": [sorted(f) for f in cl_jac],
        "familias_cosseno": [sorted(f) for f in cl_cos],
        "cliques_identicos": [sorted(f) for f in (set(cl_jac) & set(cl_cos))],
        "concordancia_arestas_pct": round((len(ambos) + nenhum) / pares_totais * 100, 1),
        "jaccard_de_arestas_pct": round(len(ambos) / len(uniao) * 100, 1) if uniao else 0.0,
        "arestas_so_jaccard": [sorted((vertices_region[i], vertices_region[j]))
                               for i, j in sorted(e_jac - e_cos)],
        "arestas_so_cosseno": [sorted((vertices_region[i], vertices_region[j]))
                               for i, j in sorted(e_cos - e_jac)],
        "clique_asiatico_em_jaccard": asia in set(cl_jac),
        "clique_asiatico_em_cosseno": asia in set(cl_cos),
    }


def _secao_familias_ingredientes(percentil=0.01):
    with redirect_stdout(_lixo):
        g, limiar, _ = cosseno.construir_grafo_projetado(ing_idx, graph, percentil_top=percentil)
    cliques = encontrar_cliques_maximos(g)
    grandes = sorted((c for c in cliques if len(c) > 2), key=len, reverse=True)
    return {
        "percentil": percentil,
        "limiar_calculado": round(limiar, 4),
        "n_cliques_total": len(cliques),
        "n_cliques_grandes": len(grandes),
        "maior_clique": max((len(c) for c in grandes), default=0),
        "exemplos_maiores": [[ID_PARA_NOME[v] for v in sorted(c)] for c in grandes[:5]],
    }


def _secao_varredura(top_k):
    jac, cos = [], []
    for lim in (0.15, 0.20, 0.25, 0.30):
        g = _grafo_jaccard(lim, top_k)
        cl = _familias(g)
        jac.append({"limiar": lim, "arestas": len(_arestas(g)),
                    "familias": len(cl), "maior": max((len(c) for c in cl), default=0)})
    for pc in (0.05, 0.10, 0.15, 0.20):
        g, lim, _ = _grafo_cosseno(pc)
        cl = _familias(g)
        cos.append({"percentil": pc, "limiar": round(lim, 4), "arestas": len(_arestas(g)),
                    "familias": len(cl), "maior": max((len(c) for c in cl), default=0)})
    return {"jaccard": jac, "cosseno": cos}


# ----------------------------------------------------------------------------
# visualizações: chama os scripts de desenho do projeto com os pesos escolhidos
# ----------------------------------------------------------------------------
def _img(nome):
    """Caminho de imagem seguro para markdown (espaços viram %20)."""
    return nome.replace(" ", "%20")


def _slug(texto):
    """Âncora no padrão do GitHub: minúsculas, sem pontuação, espaços viram '-'.
    Mantém o sumário sincronizado com os títulos das seções."""
    s = re.sub(r"[^\w\s-]", "", texto.lower())
    return re.sub(r"\s+", "-", s.strip())


def _gerar_visualizacoes(limiar_jaccard, top_k, regioes):
    """Reaproveita visualizacao.py e visualizacao_similaridade.py para gerar os
    PNGs com os parâmetros escolhidos. Devolve os nomes dos arquivos gerados."""
    figs = {"regioes": []}
    with redirect_stdout(_lixo):
        vis_sim.gerar(limiar_jaccard, top_k)  # heatmap + famílias no limiar/top-k pedidos
        vis.modo_panorama()                  # panorama_bipartido.png
        vis.modo_top()                       # top_arestas.png
        for reg in regioes:
            if reg in region_idx:
                vis.modo_regiao(reg)         # regiao_{reg}.png
                figs["regioes"].append(reg)
    figs["similaridade"] = "similaridade_regioes.png"
    figs["panorama"] = "panorama_bipartido.png"
    figs["top"] = "top_arestas.png"
    return figs


# ----------------------------------------------------------------------------
# renderização do markdown
# ----------------------------------------------------------------------------
def _render_md(R, figs):
    p = R["panorama"]; c = R["conectividade"]; f = R["familias_regioes"]
    fi = R["familias_ingredientes"]; par = R["parametros"]; vv = R["varredura"]
    L = []
    w = L.append

    secoes = [
        "Panorama do grafo bipartido",
        "Assinatura regional por TF-IDF",
        "Conectividade e distâncias (fila e BFS)",
        "Famílias de regiões (Bron–Kerbosch sobre a similaridade)",
        "Famílias de ingredientes (projeção ingrediente-ingrediente)",
        "Sensibilidade ao limiar",
    ]

    w("# Relatório de Análise — Grafo Culinário (CulinaryDB)\n")
    w(f"*Documento gerado automaticamente em {date.today().strftime('%d/%m/%Y')}.*\n")

    w("| | |")
    w("|---|---|")
    w("| **Base de dados** | CulinaryDB |")
    w("| **Modelagem** | grafo bipartido região ↔ ingrediente |")
    w("| **Peso das arestas** | TF-IDF (frequência regional normalizada) |")
    w("| **Algoritmos** | BFS, Bron–Kerbosch, similaridade de Jaccard e de cosseno |")
    w(f"| **Limiar de Jaccard** | {par['limiar_jaccard']} |")
    w(f"| **Percentil do cosseno** | {int(par['percentil_cosseno']*100)}% |")
    w(f"| **Assinatura regional** | top-{par['top_k']} ingredientes por TF-IDF |")
    w("")
    w("---\n")

    w("## Sumário\n")
    for i, t in enumerate(secoes, 1):
        w(f"{i}. [{t}](#{i}-{_slug(t)})")
    w("\n---\n")

    w(f"## 1. {secoes[0]}\n")
    w(f"- **{p['n_regioes']} regiões**, **{p['n_ingredientes']} ingredientes**, "
      f"**{p['n_arestas']} arestas** região↔ingrediente.")
    w(f"- Densidade bipartida: **{p['densidade_bipartida']*100:.1f}%**.")
    w(f"- Grau por região: min **{p['grau_regiao_min']}**, médio **{p['grau_regiao_medio']}**, "
      f"máx **{p['grau_regiao_max']}**.\n")
    w("| região | ingrediente | TF-IDF |")
    w("|---|---|---|")
    for e in p["top_exclusivos"]:
        w(f"| {e['regiao']} | {e['ingrediente']} | {e['tfidf']} |")
    w("")
    if figs.get("panorama"):
        w(f"![Panorama bipartido Região ↔ Ingrediente]({_img(figs['panorama'])})\n")
    if figs.get("top"):
        w(f"![Arestas de maior peso TF-IDF]({_img(figs['top'])})\n")

    w(f"## 2. {secoes[1]}\n")
    for reg, lst in R["assinaturas"].items():
        w(f"- **{reg}**: {', '.join(i['ingrediente'] for i in lst[:6])}")
    w("")
    for reg in figs.get("regioes", []):
        w(f"![Ingredientes-assinatura de {reg}]({_img(f'regiao_{reg}.png')})\n")

    w(f"\n## 3. {secoes[2]}\n")
    w(f"- Grafo **{'conexo' if c['grafo_conexo'] else 'NÃO conexo'}**: "
      f"alcançam-se {c['vertices_alcancados_de_0']}/{c['vertices_totais']} vértices.")
    w(f"- **Diâmetro região↔região: {c['diametro_regiao_regiao']} arestas** "
      f"(2 = compartilham um ingrediente).\n")
    w("**Ingrediente-ponte entre cozinhas distintas** (caminho mínimo BFS, desempate por TF-IDF):\n")
    w("| de | para | distância | ingrediente(s)-ponte |")
    w("|---|---|---|---|")
    for e in c["exemplos_ponte"]:
        w(f"| {e['de']} | {e['para']} | {e['distancia']} | {', '.join(e['ponte']) or '—'} |")

    w(f"\n## 4. {secoes[3]}\n")
    w(f"- **Jaccard** (assinatura top-{par['top_k']}), limiar {par['limiar_jaccard']}: "
      f"**{f['arestas_jaccard']} arestas**.")
    w(f"- **Cosseno** (vetor TF-IDF completo), percentil {int(par['percentil_cosseno']*100)}% "
      f"→ limiar {f['limiar_cosseno_calculado']}: **{f['arestas_cosseno']} arestas**.")
    w(f"- Concordância: acordo total {f['concordancia_arestas_pct']}%, "
      f"Jaccard-de-arestas **{f['jaccard_de_arestas_pct']}%**.\n")
    if figs.get("similaridade"):
        w(f"![Heatmap de Jaccard + famílias culinárias (limiar {par['limiar_jaccard']})]"
          f"({_img(figs['similaridade'])})\n")
    w("**Famílias por Jaccard:**")
    for fam in f["familias_jaccard"]:
        w(f"  - ({len(fam)}) {', '.join(fam)}")
    w("\n**Famílias por Cosseno:**")
    for fam in f["familias_cosseno"]:
        w(f"  - ({len(fam)}) {', '.join(fam)}")
    w("\n**Famílias idênticas nas duas lentes (robustas):**")
    for fam in f["cliques_identicos"]:
        w(f"  - ({len(fam)}) {', '.join(fam)}")
    w(f"\n- Clique asiático *china/korea/south east asia/thailand*: "
      f"Jaccard = {'sim' if f['clique_asiatico_em_jaccard'] else 'não'}, "
      f"Cosseno = {'sim' if f['clique_asiatico_em_cosseno'] else 'não'}.")

    w(f"\n## 5. {secoes[4]}\n")
    w(f"- Percentil {int(fi['percentil']*100)}% → limiar {fi['limiar_calculado']}; "
      f"**{fi['n_cliques_total']} cliques**, {fi['n_cliques_grandes']} com >2 elementos, "
      f"maior com **{fi['maior_clique']}**.")
    for grp in fi["exemplos_maiores"]:
        amostra = ", ".join(grp[:8]) + (f" (+{len(grp)-8})" if len(grp) > 8 else "")
        w(f"  - ({len(grp)}) {amostra}")

    w(f"\n## 6. {secoes[5]}\n")
    w("| método | parâmetro | arestas | famílias | maior clique |")
    w("|---|---|---|---|---|")
    for r in vv["jaccard"]:
        w(f"| Jaccard | limiar {r['limiar']} | {r['arestas']} | {r['familias']} | {r['maior']} |")
    for r in vv["cosseno"]:
        w(f"| Cosseno | {int(r['percentil']*100)}% (lim {r['limiar']}) | {r['arestas']} | {r['familias']} | {r['maior']} |")
    w("")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------
# API pública
# ----------------------------------------------------------------------------
def gerar(limiar_jaccard=LIMIAR_JACCARD, percentil_cosseno=PERCENTIL_COSSENO,
          top_k=TOP_K, regioes=None, com_figuras=True):
    """Roda toda a análise para os pesos dados e grava relatorio.md + resultados.json."""
    regioes = regioes if regioes is not None else DEFAULT_REGIOES
    print(f"Gerando relatório (limiar Jaccard={limiar_jaccard}, "
          f"percentil cosseno={percentil_cosseno}, top-k={top_k})...")

    R = {
        "parametros": {"limiar_jaccard": limiar_jaccard,
                       "percentil_cosseno": percentil_cosseno, "top_k": top_k},
        "panorama": _secao_panorama(),
        "assinaturas": _secao_assinaturas(),
        "conectividade": _secao_conectividade(),
        "familias_regioes": _secao_familias_regioes(limiar_jaccard, percentil_cosseno, top_k),
        "familias_ingredientes": _secao_familias_ingredientes(),
        "varredura": _secao_varredura(top_k),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    if com_figuras:
        print("  desenhando visualizações (heatmap, panorama, regiões)...")
        figs = _gerar_visualizacoes(limiar_jaccard, top_k, regioes)
    else:
        figs = {"regioes": []}

    with open(OUT_DIR / "resultados.json", "w", encoding="utf-8") as fh:
        json.dump(R, fh, indent=2, ensure_ascii=False)
    with open(OUT_DIR / "relatorio.md", "w", encoding="utf-8") as fh:
        fh.write(_render_md(R, figs))

    print(f"  -> {OUT_DIR / 'relatorio.md'}")
    print(f"  -> {OUT_DIR / 'resultados.json'}")
    if com_figuras:
        n = len(figs["regioes"]) + 3
        print(f"  -> {n} visualizações em {OUT_DIR}")
    return R


if __name__ == "__main__":
    gerar()
