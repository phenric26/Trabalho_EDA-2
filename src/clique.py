def encontrar_cliques_maximos(grafo_do_grupo):
    """
    Função principal da Etapa 4.
    Recebe o grafo do grupo {id: [(vizinho_id, peso), ...]}
    e retorna uma lista com os cliques máximos encontrados.
    """
    # Monta um grafo simples {vertice: {vizinhos}}, sem o peso,
    # porque pra achar clique só importa "tem aresta ou não tem".
    vizinhos_de = {}
    for vertice, lista_vizinhos in grafo_do_grupo.items():
        vizinhos_de[vertice] = {vizinho for vizinho, peso in lista_vizinhos}

    cliques_encontrados = []
    todos_vertices = set(vizinhos_de.keys())

    _bron_kerbosch(
        clique_atual=set(),
        candidatos=todos_vertices,
        ja_visitados=set(),
        vizinhos_de=vizinhos_de,
        cliques_encontrados=cliques_encontrados,
    )

    return cliques_encontrados


def _bron_kerbosch(clique_atual, candidatos, ja_visitados, vizinhos_de, cliques_encontrados):
    """
    Algoritmo de Bron-Kerbosch com escolha de pivô.

    clique_atual : vértices que já sabemos que formam um clique até agora
    candidatos   : vértices que ainda podem entrar nesse clique
    ja_visitados : vértices já testados nessa "ramificação", pra não repetir clique

    Por que o pivô é necessário:
    Sem ele, o algoritmo testa TODO candidato, um por um, mesmo quando dois
    candidatos levam praticamente ao mesmo resultado. Em grupos de vértices
    muito parecidos entre si (ex: ingredientes quase-sinônimos, todos
    conectados a quase todo mundo), isso faz o número de chamadas explodir
    exponencialmente e o programa "trava" (na prática, fica processando por
    muito tempo).

    A ideia do pivô: escolhe-se um vértice "pivô" que já cobre o máximo de
    candidatos possível como seus próprios vizinhos. Só testamos os
    candidatos que NÃO são vizinhos do pivô -- os demais já vão aparecer de
    qualquer forma em outro ramo da recursão através do próprio pivô. Isso
    elimina ramos redundantes sem mudar o resultado final.
    """
    if not candidatos and not ja_visitados:
        cliques_encontrados.append(clique_atual)
        return

    uniao_candidatos_visitados = candidatos | ja_visitados
    pivo = max(uniao_candidatos_visitados, key=lambda v: len(vizinhos_de[v] & candidatos))

    candidatos_a_testar = candidatos - vizinhos_de[pivo]

    for vertice in candidatos_a_testar:
        vizinhos = vizinhos_de[vertice]

        _bron_kerbosch(
            clique_atual | {vertice},      # adiciona o vértice ao clique
            candidatos & vizinhos,         # só seguem candidatos quem é vizinho dele
            ja_visitados & vizinhos,       # idem para os já visitados
            vizinhos_de,
            cliques_encontrados,
        )

        # Esse vértice já foi totalmente explorado como possibilidade:
        # remove dos candidatos e marca como visitado, pra não testar de novo.
        candidatos.remove(vertice)
        ja_visitados.add(vertice)