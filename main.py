from src.clique import encontrar_cliques_maximos
from src.bfs import bfs, reconstruir_caminho
from collections import defaultdict

PERCENTIL_REGIAO = 0.10        # mantém só o top 10% das similaridades região-região
PERCENTIL_INGREDIENTE = 0.01   # mantém só o top 1% das similaridades ingrediente-ingrediente
MAX_CLIQUES_EXIBIDOS = 8       # quantos cliques (os maiores) imprimir por projeção
MAX_NOMES_POR_CLIQUE = 4       # quantos nomes mostrar dentro de cada clique

RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"

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


def rodar_projecao(nome_projecao, descricao_clique, lado_a_idx, graph,
                    percentil_top, id_para_nome):
    print(f"\n[Projetando] Grafo {nome_projecao} (top {percentil_top*100:.1f}% das similaridades)...")
    grafo_projetado, limiar, total_pares = construir_grafo_projetado(
        lado_a_idx, graph, percentil_top
    )

    total_arestas = sum(len(v) for v in grafo_projetado.values()) // 2
    densidade = (total_arestas / total_pares * 100) if total_pares else 0
    print(f"   {total_pares} pares possíveis avaliados | limiar calculado = {limiar:.4f}")
    print(f"   {len(grafo_projetado)} vértices, {total_arestas} arestas criadas "
          f"({densidade:.1f}% de densidade).")

    print(f"[Bron-Kerbosch] Buscando cliques máximos no grafo {nome_projecao}...")
    cliques = encontrar_cliques_maximos(grafo_projetado)
    cliques_grandes = sorted(
        (c for c in cliques if len(c) > 2), key=len, reverse=True
    )

    print(f"   {len(cliques)} cliques máximos no total, "
          f"{len(cliques_grandes)} com mais de 2 elementos.")
    print(f"   Significado: {descricao_clique}")

    if not cliques_grandes:
        print("   Nenhum clique com mais de 2 elementos. "
              "Tente aumentar o percentil (deixa entrar mais arestas).")
    else:
        tamanhos = [len(c) for c in cliques_grandes]
        print(f"   Tamanho dos cliques: maior={max(tamanhos)}, "
              f"menor={min(tamanhos)}, média={sum(tamanhos)/len(tamanhos):.1f}")

        limite_exibicao = min(MAX_CLIQUES_EXIBIDOS, len(cliques_grandes))
        print(f"   Mostrando os {limite_exibicao} maiores:")
        for i, c in enumerate(cliques_grandes[:limite_exibicao], 1):
            todos_nomes = [id_para_nome.get(v, f"ID Desconhecido ({v})") for v in c]
            nomes_exibidos = todos_nomes[:MAX_NOMES_POR_CLIQUE]
            texto_nomes = ", ".join(nomes_exibidos)
            if len(todos_nomes) > MAX_NOMES_POR_CLIQUE:
                texto_nomes += f" (+{len(todos_nomes) - MAX_NOMES_POR_CLIQUE} mais)"
            print(f"     Clique #{i} ({len(c)} elementos): {texto_nomes}")

        if len(cliques_grandes) > limite_exibicao:
            print(f"     ... e mais {len(cliques_grandes) - limite_exibicao} "
                  f"cliques omitidos (aumente MAX_CLIQUES_EXIBIDOS pra ver todos).")

    return cliques


def main():
    print("=== Pipeline do Projeto Trabalho_EDA-2 ===")

    print("\n[Passo 1] Construindo e carregando o grafo bipartido (Região <-> Ingrediente)...")
    from src.grafo import graph, region_idx, ing_idx

    print(f"\n{BOLD}{GREEN} ### [BFS] ###{RESET}")

    # inicio = next(iter(region_idx.values()))
    print(f"\n{CYAN}Escolha a região inicial do BFS:{RESET}\n")

    regioes = list(region_idx.keys())

    for i, nome in enumerate(regioes):
        print(f"{i} - {nome}")

    escolha = int(input("\nDigite o número da região: "))

    if escolha < 0 or escolha >= len(regioes):
        raise ValueError("Escolha inválida!")

    nome_regiao = regioes[escolha]
    inicio = region_idx[nome_regiao]

    print(f"\n[BFS] Região escolhida: {nome_regiao}")

    distancias, pais = bfs(graph, inicio)

    print(f"   Vértices alcançados: {len(distancias)}")

# agrupa por camada (distância)
    camadas = defaultdict(list)

    for v, d in distancias.items():
        camadas[d].append(v)

    id_para_nome = {}
    for reg_nome, idx in region_idx.items():
        id_para_nome[idx] = f"Região: {reg_nome.upper()}"
    for ing_nome, idx in ing_idx.items():
        id_para_nome[idx] = f"Ingrediente: {ing_nome}"

    print("\n   Camadas BFS:")

    for d in sorted(camadas.keys()):
        print(f"\n   Distância {d} ({len(camadas[d])} nós):")

        for v in camadas[d][:10]:
            nome = id_para_nome.get(v, f"Nó {v}")
            print(f"     {nome}")


    print(f"\n\n  Grafo bipartido carregado: {len(region_idx)} regiões, "
          f"{len(ing_idx)} ingredientes.")

    print("\n[Aviso] Esse grafo é BIPARTIDO (só existem arestas Região<->Ingrediente).")
    print("        Por isso todo clique máximo nele tem exatamente 2 elementos --")
    print("        não há grupos de 3+ pra analisar diretamente.")
    print("        Solução: projetar o grafo bipartido em dois grafos unipartidos,")
    print("        mantendo só os pares mais parecidos (top X%), e procurar")
    print("        cliques neles.")

    # ===================== Projeção A: Região-Região =====================
    rodar_projecao(
        nome_projecao="Região-Região",
        descricao_clique="cada clique é um GRUPO DE REGIÕES cuja culinária é "
                          "mutuamente parecida (compartilham ingredientes com "
                          "pesos TF-IDF semelhantes).",
        lado_a_idx=region_idx,
        graph=graph,
        percentil_top=PERCENTIL_REGIAO,
        id_para_nome=id_para_nome,
    )

    # ================ Projeção B: Ingrediente-Ingrediente ================
    rodar_projecao(
        nome_projecao="Ingrediente-Ingrediente",
        descricao_clique="cada clique é um GRUPO DE INGREDIENTES que tende a "
                          "ter o mesmo padrão de uso regional (aparecem nas "
                          "mesmas regiões, com pesos parecidos) -- uma possível "
                          "'assinatura' de cozinha.",
        lado_a_idx=ing_idx,
        graph=graph,
        percentil_top=PERCENTIL_INGREDIENTE,
        id_para_nome=id_para_nome,
    )

    print("\n=== Pipeline concluído ===")


if __name__ == "__main__":
    main()