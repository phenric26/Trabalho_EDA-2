"""Similaridade de Jaccard entre regiões e detecção de famílias por clique."""

import argparse

from grafo import graph, vertices_region
from clique import encontrar_cliques_maximos

LIMIAR_PADRAO = 0.20
TOP_K_ASSINATURA = 30

N_REGIOES = len(vertices_region)


def conjuntos_de_ingredientes(top_k=TOP_K_ASSINATURA):
    # cada região representada pelos seus top_k ingredientes de maior peso
    sets = {}
    for r in range(N_REGIOES):
        vizinhos = sorted(graph.get(r, []), key=lambda x: -x[1])[:top_k]
        sets[r] = {viz for viz, _ in vizinhos}
    return sets


def jaccard(a, b):
    if not a and not b:
        return 0.0
    uniao = len(a | b)
    return len(a & b) / uniao if uniao else 0.0


def matriz_jaccard():
    sets = conjuntos_de_ingredientes()
    return [[jaccard(sets[i], sets[j]) for j in range(N_REGIOES)]
            for i in range(N_REGIOES)]


def grafo_similaridade(limiar=LIMIAR_PADRAO):
    # devolve no formato {id: [(vizinho, peso), ...]} consumido por encontrar_cliques_maximos
    sets = conjuntos_de_ingredientes()
    g = {i: [] for i in range(N_REGIOES)}
    for i in range(N_REGIOES):
        for j in range(i + 1, N_REGIOES):
            s = jaccard(sets[i], sets[j])
            if s >= limiar:
                peso = round(s, 4)
                g[i].append((j, peso))
                g[j].append((i, peso))
    return g


def familias_culinarias(limiar=LIMIAR_PADRAO):
    g = grafo_similaridade(limiar)
    cliques = encontrar_cliques_maximos(g)
    cliques = sorted((sorted(c) for c in cliques), key=len, reverse=True)
    return cliques, g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limiar", type=float, default=LIMIAR_PADRAO)
    args = ap.parse_args()

    print(f"Regiões: {N_REGIOES} | limiar de Jaccard = {args.limiar}\n")

    cliques, g = familias_culinarias(args.limiar)
    grau = {i: len(v) for i, v in g.items()}
    n_arestas = sum(grau.values()) // 2
    print(f"Grafo de similaridade: {n_arestas} arestas (pares acima do limiar)\n")

    familias = [c for c in cliques if len(c) >= 2]
    print(f"Famílias (cliques de tamanho >= 2): {len(familias)}")
    for k, c in enumerate(familias, 1):
        print(f"  família {k}: {', '.join(vertices_region[i] for i in c)}")

    isoladas = [vertices_region[i] for i in range(N_REGIOES) if grau[i] == 0]
    if isoladas:
        print(f"\nRegiões sem vizinha acima do limiar: {', '.join(isoladas)}")


if __name__ == "__main__":
    main()
