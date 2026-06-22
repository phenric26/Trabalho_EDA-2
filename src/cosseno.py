"""Similaridade do cosseno + projeção do grafo bipartido (contribuição do colega).

Funções extraídas do antigo main.py SEM alteração de lógica: calculam a
similaridade do cosseno entre vértices de um mesmo lado (Região ou Ingrediente)
usando os pesos TF-IDF do grafo bipartido, e projetam um grafo unipartido
mantendo só os pares mais fortes (top percentil).

É só algoritmo do grupo — não importa matplotlib/networkx nem o grafo; recebe a
lista de adjacência por parâmetro. O orquestrador (relatorio.py) consome estas
funções; main.py virou um entrypoint fino.
"""


def construir_mapa_pesos(vertice_id, graph):
    """Converte a lista de adjacência [(vizinho, peso), ...] de um vértice
    em um dicionário {vizinho: peso}, pra facilitar consulta direta."""
    return {viz: w for viz, w in graph[vertice_id]}


def calcular_similaridades(lado_a_idx, graph):
    """
    Calcula a similaridade do cosseno entre TODOS os pares de vértices do
    lado A (Região ou Ingrediente), usando os pesos TF-IDF que cada um tem
    com o lado B do grafo bipartido original.

    Devolve uma lista de tuplas (vertice1, vertice2, similaridade),
    SEM aplicar limiar nenhum ainda -- isso é feito depois, baseado no
    percentil escolhido.
    """
    ids_a = list(lado_a_idx.values())
    vetores = {a: construir_mapa_pesos(a, graph) for a in ids_a}
    normas = {a: sum(p * p for p in v.values()) ** 0.5 for a, v in vetores.items()}

    similaridades = []
    for i in range(len(ids_a)):
        a1 = ids_a[i]
        v1 = vetores[a1]
        n1 = normas[a1]
        if n1 == 0:
            continue

        for j in range(i + 1, len(ids_a)):
            a2 = ids_a[j]
            v2 = vetores[a2]
            n2 = normas[a2]
            if n2 == 0:
                continue

            comuns = v1.keys() & v2.keys()
            if not comuns:
                continue

            produto_escalar = sum(v1[b] * v2[b] for b in comuns)
            similaridade = produto_escalar / (n1 * n2)
            similaridades.append((a1, a2, similaridade))

    return similaridades


def escolher_limiar_por_percentil(similaridades, percentil_top):
    """
    Em vez de adivinhar um número de limiar, deixamos o próprio dado decidir:
    olhamos pra distribuição real das similaridades calculadas e escolhemos
    o valor que deixa passar só os 'percentil_top' pares mais fortes.

    Exemplo: percentil_top=0.01 com 1000 pares -> mantém só os 10 mais
    parecidos (top 1%), descartando o resto -- mesmo que esses 10 tenham
    uma similaridade "baixa" em termos absolutos.
    """
    valores = sorted((sim for _, _, sim in similaridades), reverse=True)
    if not valores:
        return float("inf")  # nenhum par com similaridade > 0; ninguém conecta

    posicao = max(0, int(len(valores) * percentil_top) - 1)
    return valores[posicao]


def construir_grafo_projetado(lado_a_idx, graph, percentil_top):
    """
    Projeta o grafo bipartido (Região <-> Ingrediente) em um grafo unipartido
    sobre os vértices de `lado_a_idx`, mantendo só os pares mais parecidos
    (top `percentil_top`).

    Por quê a projeção é necessária:
    O grafo original só tem arestas Região<->Ingrediente. Num grafo bipartido,
    todo clique máximo tem tamanho 2 -- não existem cliques de 3+ elementos
    pra analisar, porque não há como dois vértices do mesmo lado estarem
    conectados entre si. A projeção cria essas arestas que faltam, baseada em
    quão parecido (similaridade do cosseno) é o uso de ingredientes de cada
    região (ou o padrão regional de cada ingrediente).
    """
    similaridades = calcular_similaridades(lado_a_idx, graph)
    limiar = escolher_limiar_por_percentil(similaridades, percentil_top)

    grafo_projetado = {a: [] for a in lado_a_idx.values()}
    for a1, a2, sim in similaridades:
        if sim >= limiar:
            grafo_projetado[a1].append((a2, round(sim, 4)))
            grafo_projetado[a2].append((a1, round(sim, 4)))

    return grafo_projetado, limiar, len(similaridades)
