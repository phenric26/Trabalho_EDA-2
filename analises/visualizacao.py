"""
networkx/matplotlib são usadospara desenhar:
não há cálculo de centralidade, comunidades, caminhos ou similaridade aqui.
As coordenadas dos nós são definidas à mão a partir da partição que já existe
em src/grafo.py; a filtragem por peso é decisão de plotagem, não de análise.
Todo número exibido (peso, grau) é lido da lista de adjacência do grupo.

"""

import sys
import os
import argparse

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src.grafo import (  # noqa: E402
    graph, region_idx, vertices_region, vertices_ingredient
)

PESO_MINIMO_PANORAMA = 0.15
TOP_N_ARESTAS = 40            
TOP_N_REGIAO = 20             
COR_REGIAO = "#d65a3a"
COR_INGREDIENTE = "#2e8b8b"
COR_ARESTA = "#9aa0b5"
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "output")

N_REGIOES = len(vertices_region)


def eh_regiao(idx):
    return idx < N_REGIOES

def nome(idx):
    return vertices_region[idx] if eh_regiao(idx) else vertices_ingredient[idx - N_REGIOES]

def arestas_unicas(peso_min=0.0):
    """Lê as arestas região->ingrediente da lista de adjacência, sem duplicar."""
    vistas = set()
    out = []
    for v, vizinhos in graph.items():
        for u, w in vizinhos:
            if w < peso_min:
                continue
            chave = (min(v, u), max(v, u))
            if chave in vistas:
                continue
            vistas.add(chave)
            out.append((v, u, w))
    return out


def posicoes_bipartidas(regioes_idx, ings_idx):
    """Regiões na coluna da esquerda, ingredientes na direita."""
    pos = {}
    for i, r in enumerate(sorted(regioes_idx)):
        y = 1.0 - (i / max(1, len(regioes_idx) - 1)) if len(regioes_idx) > 1 else 0.5
        pos[r] = (0.0, y)
    for i, ing in enumerate(sorted(ings_idx)):
        y = 1.0 - (i / max(1, len(ings_idx) - 1)) if len(ings_idx) > 1 else 0.5
        pos[ing] = (1.0, y)
    return pos


def _montar_grafo_nx(arestas):
    """nx.Graph apenas como contêiner de desenho; a topologia já está decidida."""
    G = nx.Graph()
    for v, u, w in arestas:
        G.add_node(v, tipo="regiao" if eh_regiao(v) else "ing")
        G.add_node(u, tipo="regiao" if eh_regiao(u) else "ing")
        G.add_edge(v, u, weight=w)
    return G


def _desenhar(G, pos, titulo, arquivo, rotulos_ing=None):
    """rotulos_ing: dict idx->texto. Se None, usa o nome do ingrediente.
    Se {}, não rotula ingredientes."""
    fig, ax = plt.subplots(figsize=(11, 9))

    regioes = [n for n in G if eh_regiao(n)]
    ings = [n for n in G if not eh_regiao(n)]

    pesos = [G[u][v]["weight"] for u, v in G.edges()]
    larguras = [0.4 + 3.0 * w for w in pesos]

    nx.draw_networkx_edges(G, pos, ax=ax, width=larguras,
                           edge_color=COR_ARESTA, alpha=0.6)

    nx.draw_networkx_nodes(G, pos, nodelist=regioes, ax=ax,
                           node_color=COR_REGIAO, node_size=1100,
                           edgecolors="white", linewidths=1.5)
    nx.draw_networkx_nodes(G, pos, nodelist=ings, ax=ax,
                           node_color=COR_INGREDIENTE, node_size=380,
                           edgecolors="white", linewidths=1.0)

    for n in regioes:
        x, y = pos[n]
        ax.text(x - 0.04, y, nome(n), fontsize=10, fontweight="bold",
                ha="right", va="center", color=COR_REGIAO)

    if rotulos_ing != {}:
        rotulos_ing = rotulos_ing or {n: nome(n) for n in ings}
        for n in ings:
            x, y = pos[n]
            ax.text(x + 0.03, y, rotulos_ing.get(n, nome(n)),
                    fontsize=7, ha="left", va="center", color="#2a2a2a")

    legenda = [
        Line2D([0], [0], marker="o", color="w", label="Região",
               markerfacecolor=COR_REGIAO, markersize=12),
        Line2D([0], [0], marker="o", color="w", label="Ingrediente",
               markerfacecolor=COR_INGREDIENTE, markersize=9),
        Line2D([0], [0], color=COR_ARESTA, lw=2,
               label="Aresta (espessura ∝ TF-IDF)"),
    ]
    ax.legend(handles=legenda, loc="upper center", ncol=3,
              frameon=False, bbox_to_anchor=(0.5, -0.02))
    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=14)
    ax.axis("off")
    fig.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    caminho = os.path.join(OUT_DIR, arquivo)
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  salvo: {caminho}  ({G.number_of_nodes()} nós, {G.number_of_edges()} arestas)")


def modo_panorama(peso_min=PESO_MINIMO_PANORAMA):
    print(f"[panorama] peso mínimo = {peso_min}")
    arestas = arestas_unicas(peso_min)
    G = _montar_grafo_nx(arestas)
    regioes = {n for n in G if eh_regiao(n)}
    ings = {n for n in G if not eh_regiao(n)}
    pos = posicoes_bipartidas(regioes, ings)
    rotulos = None if len(ings) <= 60 else {}   # acima de 60 o texto polui
    _desenhar(G, pos,
              f"Panorama bipartido Região ↔ Ingrediente (peso ≥ {peso_min})",
              "panorama_bipartido.png", rotulos_ing=rotulos)


def modo_regiao(regiao, top_n=TOP_N_REGIAO):
    if regiao not in region_idx:
        print(f"  região '{regiao}' não existe. Disponíveis: {', '.join(vertices_region)}")
        return
    print(f"[regiao] {regiao} (top {top_n})")
    r = region_idx[regiao]
    
    vizinhos = sorted(graph.get(r, []), key=lambda x: -x[1])[:top_n]
    arestas = [(r, u, w) for u, w in vizinhos]
    G = _montar_grafo_nx(arestas)

    pos = {r: (0.0, 0.5)}
    ings = [u for u, _ in vizinhos]
    for i, u in enumerate(ings):
        y = 1.0 - (i / max(1, len(ings) - 1)) if len(ings) > 1 else 0.5
        pos[u] = (1.0, y)

   
    rotulos = {u: f"{nome(u)}  ({w:.3f})" for u, w in vizinhos}
    _desenhar(G, pos,
              f"Top {top_n} ingredientes-assinatura de '{regiao}' (por TF-IDF)",
              f"regiao_{regiao}.png", rotulos_ing=rotulos)


def modo_top(n=TOP_N_ARESTAS):
    print(f"[top] {n} arestas de maior peso")
    arestas = sorted(arestas_unicas(), key=lambda x: -x[2])[:n]
    G = _montar_grafo_nx(arestas)
    regioes = {x for x in G if eh_regiao(x)}
    ings = {x for x in G if not eh_regiao(x)}
    pos = posicoes_bipartidas(regioes, ings)
    _desenhar(G, pos, f"Top {n} arestas por peso TF-IDF", "top_arestas.png")


def main():
    ap = argparse.ArgumentParser(description="Visualização do grafo bipartido (Etapa 5)")
    ap.add_argument("--modo", choices=["panorama", "regiao", "top", "todos"],
                    default="todos")
    ap.add_argument("--regiao", default="italy", help="região para o modo 'regiao'")
    ap.add_argument("--peso-min", type=float, default=PESO_MINIMO_PANORAMA)
    args = ap.parse_args()

    print(f"Grafo: {N_REGIOES} regiões, {len(vertices_ingredient)} ingredientes\n")

    if args.modo in ("panorama", "todos"):
        modo_panorama(args.peso_min)
    if args.modo in ("regiao", "todos"):
        modo_regiao(args.regiao)
    if args.modo in ("top", "todos"):
        modo_top()

    print(f"\nImagens em: {OUT_DIR}")


if __name__ == "__main__":
    main()
