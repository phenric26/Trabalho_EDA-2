"""
BFS (Busca em Largura) sobre o grafo bipartido Região <-> Ingrediente.

Decisão de projeto — ordenação por peso TF-IDF:
  O BFS clássico expande vértices em ordem de descoberta (FIFO puro).
  A distância medida é sempre em número de arestas, independente do peso.

  Aqui, antes de enfileirar os vizinhos de um vértice, eles são ordenados
  pelo peso TF-IDF em ordem DECRESCENTE. Isso significa que, quando dois
  vizinhos seriam descobertos na mesma "camada" do BFS, o de maior peso
  entra na fila primeiro e será visitado primeiro dentro dessa camada.

  O que isso muda:
    - As distâncias (em arestas) continuam exatas e idênticas ao BFS puro.
    - O dicionário `pais` pode diferir quando há múltiplos pais à mesma
      distância: o pai escolhido será o de maior peso TF-IDF.
    - A ordem de visita dentro de cada nível favorece ingredientes mais
      característicos da região (alto TF-IDF), tornando os caminhos
      reconstruídos mais "culinariamente relevantes".

  Isso ainda É BFS: a estrutura é FIFO, a exploração é por camadas,
  e as distâncias retornadas são corretas. A ordenação é apenas um
  critério de desempate dentro da mesma camada.

  Alternativa descartada — Dijkstra:
    Dijkstra usaria os pesos como custo acumulado e encontraria caminhos
    de menor custo total, mas perderia a garantia de menor número de arestas.
    Para este grafo bipartido onde a profundidade tem significado semântico
    (nível 1 = ingrediente direto da região, nível 2 = região vizinha, etc.),
    manter a distância em arestas é mais útil.
"""

from .fila import Fila

def bfs(graph: dict, inicio: int) -> tuple[dict, dict]:
    """
    Executa BFS a partir do vértice `inicio`.

    Parâmetros
    ----------
    graph : dict
        Lista de adjacência no formato {vertice: [(vizinho, peso), ...]}.
        Vértices ausentes do dicionário são tratados como sem vizinhos.
    inicio : int
        Índice do vértice inicial.

    Retorno
    -------
    distancias : dict[int, int]
        distancias[v] = número de arestas entre `inicio` e v.
        Vértices não alcançáveis não aparecem no dicionário.
    pais : dict[int, int | None]
        pais[v] = vértice predecessor de v no caminho BFS.
        pais[inicio] = None (raiz da árvore BFS).
        Vértices não alcançáveis não aparecem no dicionário.
    """
    distancias: dict[int, int]      = {inicio: 0}
    pais:       dict[int, int | None] = {inicio: None}
    visitados:  set[int]            = {inicio}

    fila = Fila()
    fila.enqueue(inicio)

    while not fila.is_empty():
        atual = fila.dequeue()

        # Vizinhos ordenados por peso TF-IDF decrescente.
        # Dentro da mesma camada BFS, os de maior relevância culinária
        # são enfileirados primeiro e, portanto, visitados primeiro.
        vizinhos = graph.get(atual, [])
        vizinhos_ordenados = sorted(vizinhos, key=lambda par: par[1], reverse=True)

        for vizinho, _ in vizinhos_ordenados:
            if vizinho not in visitados:
                visitados.add(vizinho)
                distancias[vizinho] = distancias[atual] + 1
                pais[vizinho]       = atual
                fila.enqueue(vizinho)

    return distancias, pais


def reconstruir_caminho(pais: dict, destino: int) -> list[int]:
    """
    Reconstrói o caminho da raiz BFS até `destino` usando o dicionário `pais`.

    O caminho é reconstruído de trás para frente (destino → raiz)
    percorrendo os predecessores, depois invertido.

    Parâmetros
    ----------
    pais : dict[int, int | None]
        Dicionário retornado por bfs().
    destino : int
        Vértice de destino.

    Retorno
    -------
    list[int]
        Lista de vértices do caminho [inicio, ..., destino].
        Lista vazia se `destino` não foi alcançado pelo BFS.
    """
    if destino not in pais:
        return []   # vértice não alcançado

    caminho = []
    atual   = destino

    while atual is not None:
        caminho.append(atual)
        atual = pais[atual]

    caminho.reverse()
    return caminho
