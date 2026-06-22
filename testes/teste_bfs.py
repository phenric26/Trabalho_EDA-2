"""
Testes do BFS sobre o grafo bipartido culinário.

Como executar (a partir da raiz do projeto, onde fica src/):
    python teste_bfs.py

O arquivo assume que grafo.py está em src/ e expõe:
    graph       → dict  {int: [(int, float)]}
    region_idx  → dict  {str: int}
    ing_idx     → dict  {str: int}
    vertices_region     → list[str]
    vertices_ingredient → list[str]
"""

import sys
import os

# Garante que src/ está no path para que os imports funcionem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from grafo import graph, region_idx, ing_idx, vertices_region, vertices_ingredient
from bfs import bfs, reconstruir_caminho


# ── helpers de exibição ────────────────────────────────────────────────────── #

def nome_vertice(idx: int) -> str:
    """Converte índice numérico de volta para o nome legível."""
    n_regioes = len(vertices_region)
    if idx < n_regioes:
        return f"[região] {vertices_region[idx]}"
    return f"[ingrediente] {vertices_ingredient[idx - n_regioes]}"


def exibir_caminho(pais: dict, destino: int) -> None:
    caminho = reconstruir_caminho(pais, destino)
    if not caminho:
        print("  → Vértice não alcançado.")
        return
    nomes = [nome_vertice(v) for v in caminho]
    print("  → " + "  →  ".join(nomes))


# ── Teste 1: Fila isolada ─────────────────────────────────────────────────── #

def teste_fila():
    print("=" * 60)
    print("TESTE 1 — Fila (lista encadeada)")
    print("=" * 60)

    from fila.fila import Fila
    f = Fila()

    assert f.is_empty(), "Fila deve começar vazia"
    assert f.size() == 0

    f.enqueue(10)
    f.enqueue(20)
    f.enqueue(30)

    assert f.size()  == 3
    assert f.peek()  == 10, "peek deve retornar frente sem remover"
    assert f.size()  == 3,  "peek não deve alterar tamanho"

    assert f.dequeue() == 10
    assert f.dequeue() == 20
    assert f.size()    == 1
    assert not f.is_empty()

    assert f.dequeue() == 30
    assert f.is_empty()

    # Testa exceções
    try:
        f.dequeue()
        assert False, "Deveria lançar IndexError"
    except IndexError:
        pass

    try:
        f.peek()
        assert False, "Deveria lançar IndexError"
    except IndexError:
        pass

    print("  Todos os asserts passaram.\n")


# ── Teste 2: BFS em grafo mínimo conhecido ───────────────────────────────── #

def teste_bfs_grafo_minimo():
    """
    Grafo bipartido mínimo para verificação manual:

        região 0 (japan)
        ├── ing 2 (soy sauce)   peso 0.9
        ├── ing 3 (miso)        peso 0.7
        └── ing 4 (rice)        peso 0.3

        região 1 (korea)
        ├── ing 3 (miso)        peso 0.5
        └── ing 4 (rice)        peso 0.8

    Distâncias esperadas a partir do vértice 0 (japan):
        0 → 0 : 0
        0 → 2 : 1
        0 → 3 : 1
        0 → 4 : 1
        0 → 1 : 2  (japan → rice → korea  ou  japan → miso → korea)
    """
    print("=" * 60)
    print("TESTE 2 — BFS em grafo mínimo conhecido")
    print("=" * 60)

    grafo_mini = {
        0: [(2, 0.9), (3, 0.7), (4, 0.3)],
        1: [(3, 0.5), (4, 0.8)],
        2: [(0, 0.9)],
        3: [(0, 0.7), (1, 0.5)],
        4: [(0, 0.3), (1, 0.8)],
    }

    dist, pais = bfs(grafo_mini, 0)

    assert dist[0] == 0
    assert dist[2] == 1
    assert dist[3] == 1
    assert dist[4] == 1
    assert dist[1] == 2, f"Esperado 2, obtido {dist[1]}"

    # Com ordenação por peso desc, os vizinhos de 0 são enfileirados:
    # soy_sauce(0.9), miso(0.7), rice(0.3)
    # Portanto o primeiro vizinho de nível-1 a ser expandido é 2 (soy_sauce),
    # que não conecta a 1. O segundo é 3 (miso), que conecta a 1:
    #   pais[1] deve ser 3 (miso), não 4 (rice).
    assert pais[1] == 3, (
        f"Com ordenação por peso, pais[1] deveria ser 3 (miso, peso 0.7), "
        f"mas foi {pais[1]}"
    )

    print(f"  dist  = {dist}")
    print(f"  pais  = {pais}")
    print(f"  caminho 0→1: {reconstruir_caminho(pais, 1)}")
    print("  Todos os asserts passaram.\n")


# ── Teste 3: BFS no grafo real ───────────────────────────────────────────── #

def teste_bfs_real(regiao_origem: str = "japan"):
    print("=" * 60)
    print(f"TESTE 3 — BFS no grafo real  (origem: {regiao_origem})")
    print("=" * 60)

    if regiao_origem not in region_idx:
        print(f"  Região '{regiao_origem}' não encontrada no grafo.")
        return

    inicio = region_idx[regiao_origem]
    dist, pais = bfs(graph, inicio)

    n_regioes      = len(vertices_region)
    n_ingredientes = len(vertices_ingredient)

    regioes_alcancadas      = [v for v in dist if v < n_regioes]
    ingredientes_alcancados = [v for v in dist if v >= n_regioes]

    print(f"  Vértice inicial : {inicio} ({regiao_origem})")
    print(f"  Vértices alcançados: {len(dist)} "
          f"({len(regioes_alcancadas)} regiões + {len(ingredientes_alcancados)} ingredientes)")

    # Top 10 ingredientes mais próximos (dist == 1, ordenados pelo índice)
    diretos = sorted(
        [(v, dist[v]) for v in ingredientes_alcancados if dist[v] == 1],
        key=lambda x: x[0]
    )
    print(f"\n  Ingredientes diretos (dist=1): {len(diretos)} total")
    print("  Primeiros 10:")
    for v, d in diretos[:10]:
        nome = vertices_ingredient[v - n_regioes]
        print(f"    [{v}] {nome}  (dist={d})")

    # Regiões alcançadas e suas distâncias
    print(f"\n  Regiões alcançadas (dist ≥ 2):")
    for v in sorted(regioes_alcancadas):
        if v == inicio:
            continue
        nome = vertices_region[v]
        print(f"    [{v}] {nome}  (dist={dist[v]})")

    # Exemplo de caminho entre duas regiões
    destino_nome = "italy"
    if destino_nome in region_idx:
        destino = region_idx[destino_nome]
        print(f"\n  Caminho {regiao_origem} → {destino_nome}:")
        exibir_caminho(pais, destino)


# ── Teste 4: reconstruir_caminho — casos de borda ───────────────────────── #

def teste_reconstruir_caminho():
    print("=" * 60)
    print("TESTE 4 — reconstruir_caminho (casos de borda)")
    print("=" * 60)

    # Destino não alcançado
    caminho = reconstruir_caminho({0: None}, destino=99)
    assert caminho == [], f"Esperado [], obtido {caminho}"

    # Caminho de tamanho 1 (origem == destino)
    caminho = reconstruir_caminho({5: None}, destino=5)
    assert caminho == [5], f"Esperado [5], obtido {caminho}"

    # Caminho linear 0 → 1 → 2
    pais = {0: None, 1: 0, 2: 1}
    caminho = reconstruir_caminho(pais, destino=2)
    assert caminho == [0, 1, 2], f"Esperado [0,1,2], obtido {caminho}"

    print("  Todos os asserts passaram.\n")


# ── Main ──────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    teste_fila()
    teste_bfs_grafo_minimo()
    teste_reconstruir_caminho()
    teste_bfs_real("japan")
    teste_bfs_real("italy")