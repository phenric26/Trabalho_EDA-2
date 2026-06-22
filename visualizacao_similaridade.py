"""Heatmap de Jaccard entre regiões e grafo das famílias (cliques)."""

import sys
import os
import argparse
import math

import matplotlib.pyplot as plt
import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from grafo import vertices_region
from analise_similaridade import (
    matriz_jaccard, grafo_similaridade, familias_culinarias, LIMIAR_PADRAO,
)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "output")
COR_NEUTRA = "#c8ccd8"


def _ordem_e_cores(cliques):
    # ordem (membros da mesma família contíguos) e cor de cada região, vindas dos cliques
    familias = [c for c in cliques if len(c) >= 2]
    paleta = plt.get_cmap("tab10")
    cor = {}
    ordem = []
    vistos = set()
    for k, fam in enumerate(familias):
        c = paleta(k % 10)
        for r in fam:
            if r not in cor:
                cor[r] = c
            if r not in vistos:
                vistos.add(r)
                ordem.append(r)
    for r in range(len(vertices_region)):
        if r not in vistos:
            ordem.append(r)
            cor.setdefault(r, COR_NEUTRA)
    return ordem, cor


def _painel_heatmap(ax, ordem):
    M = matriz_jaccard()
    Mord = [[M[i][j] for j in ordem] for i in ordem]
    rotulos = [vertices_region[i] for i in ordem]

    im = ax.imshow(Mord, cmap="YlOrRd", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(ordem)))
    ax.set_yticks(range(len(ordem)))
    ax.set_xticklabels(rotulos, rotation=90, fontsize=6)
    ax.set_yticklabels(rotulos, fontsize=6)
    ax.set_title("Similaridade de Jaccard (ordenada por família)",
                 fontsize=11, fontweight="bold", pad=10)
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Jaccard", fontsize=8)
    cb.ax.tick_params(labelsize=7)


def _posicoes_circulares(ordem):
    pos = {}
    n = len(ordem)
    for k, r in enumerate(ordem):
        ang = 2 * math.pi * k / n
        pos[r] = (math.cos(ang), math.sin(ang))
    return pos


def _painel_grafo(ax, ordem, cor, limiar):
    g = grafo_similaridade(limiar)
    G = nx.Graph()
    G.add_nodes_from(range(len(vertices_region)))
    for v, vizinhos in g.items():
        for u, w in vizinhos:
            G.add_edge(v, u, weight=w)

    pos = _posicoes_circulares(ordem)
    larguras = [0.5 + 5.0 * G[u][v]["weight"] for u, v in G.edges()]

    nx.draw_networkx_edges(G, pos, ax=ax, width=larguras,
                           edge_color="#9aa0b5", alpha=0.5)
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=[cor[r] for r in G.nodes()],
                           node_size=320, edgecolors="white", linewidths=1.2)
    for r in G.nodes():
        x, y = pos[r]
        ax.text(x * 1.12, y * 1.12, vertices_region[r], fontsize=6.5,
                ha="center", va="center")

    ax.set_title(f"Famílias culinárias (Jaccard ≥ {limiar})",
                 fontsize=11, fontweight="bold", pad=10)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.axis("off")


def gerar(limiar=LIMIAR_PADRAO):
    cliques, _ = familias_culinarias(limiar)
    ordem, cor = _ordem_e_cores(cliques)
    familias = [c for c in cliques if len(c) >= 2]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8.5))
    _painel_heatmap(ax1, ordem)
    _painel_grafo(ax2, ordem, cor, limiar)
    fig.tight_layout()

    os.makedirs(OUT_DIR, exist_ok=True)
    caminho = os.path.join(OUT_DIR, "similaridade_regioes.png")
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  salvo: {caminho}")
    print(f"  {len(familias)} famílias com limiar {limiar}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limiar", type=float, default=LIMIAR_PADRAO)
    args = ap.parse_args()
    gerar(args.limiar)


if __name__ == "__main__":
    main()
