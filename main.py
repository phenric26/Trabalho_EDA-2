"""Entrypoint do projeto Trabalho_EDA-2.

Roda o pipeline interativo do grupo sobre o grafo bipartido TF-IDF
(Região <-> Ingrediente):

  1. constrói/carrega o grafo bipartido;
  2. BFS a partir de um vértice escolhido (região OU ingrediente),
     mostrando os vértices alcançados por camada (distância);
  3. projeção por similaridade de cosseno + Bron-Kerbosch, achando as
     "famílias" de regiões e de ingredientes mutuamente parecidas.

Ao final, gera o relatório consolidado em data/output/relatorio.md (com as
figuras embutidas) usando os mesmos pesos passados por flag, e avisa onde
encontrá-lo. Assim o pipeline interativo e o relatório convivem no mesmo
entrypoint.

Exemplos:
    uv run python3 main.py
    uv run python3 main.py --limiar 0.25 --percentil 0.05 --top-k 40
    uv run python3 main.py --sem-interativo                 # pula os prompts do BFS
    uv run python3 main.py --sem-figuras                    # relatório só em markdown
"""

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from clique import encontrar_cliques_maximos      # noqa: E402
from fila.bfs import bfs                           # noqa: E402
from cosseno import construir_grafo_projetado      # noqa: E402
import relatorio                                    # noqa: E402

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


def rodar_projecao(nome_projecao, descricao_clique, lado_a_idx, graph,
                   percentil_top, id_para_nome):
    """Projeta o grafo bipartido em um grafo unipartido (cosseno) e procura
    cliques máximos nele com Bron-Kerbosch, imprimindo um resumo no console."""
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


def escolher_inicio_bfs(region_idx, ing_idx, interativo):
    """Pergunta ao usuário o vértice inicial do BFS (tipo + nome).

    Com `interativo=False`, devolve a primeira região (sem prompts), para que o
    pipeline rode de ponta a ponta de forma scriptável."""
    nomes_regiao = list(region_idx.keys())
    if not interativo:
        nome = nomes_regiao[0]
        return region_idx[nome], "região", nome

    print(f"\n{CYAN}Escolha o tipo de vértice inicial do BFS:{RESET}\n")
    print("0 - Região")
    print("1 - Ingrediente")
    tipo_escolha = int(input("\nDigite o tipo (0 ou 1): "))
    if tipo_escolha not in (0, 1):
        raise ValueError("Escolha inválida!")

    fonte_idx = region_idx if tipo_escolha == 0 else ing_idx
    rotulo = "região" if tipo_escolha == 0 else "ingrediente"

    print(f"\n{CYAN}Escolha o {rotulo} inicial do BFS:{RESET}\n")
    nomes_fonte = list(fonte_idx.keys())
    for i, nome in enumerate(nomes_fonte):
        print(f"{i} - {nome}")

    escolha = int(input(f"\nDigite o número do {rotulo}: "))
    if escolha < 0 or escolha >= len(nomes_fonte):
        raise ValueError("Escolha inválida!")

    nome_escolhido = nomes_fonte[escolha]
    return fonte_idx[nome_escolhido], rotulo, nome_escolhido


def pipeline_interativo(args):
    """Pipeline do grupo: BFS por camadas + projeções (cosseno) com cliques."""
    print("=== Pipeline do Projeto Trabalho_EDA-2 ===")

    print(f"\n{BOLD}{GREEN}Construindo e carregando o grafo bipartido "
          f"(Região <-> Ingrediente)...{RESET}")
    from grafo import graph, region_idx, ing_idx
    print(f"{BOLD}{YELLOW} >> Grafo carregado: {len(region_idx)} regiões, "
          f"{len(ing_idx)} ingredientes.{RESET}")

    id_para_nome = {}
    for reg_nome, idx in region_idx.items():
        id_para_nome[idx] = f"Região: {reg_nome.upper()}"
    for ing_nome, idx in ing_idx.items():
        id_para_nome[idx] = f"Ingrediente: {ing_nome}"

    # ============================= BFS =============================
    print(f"\n{BOLD}{GREEN} ### BFS ###{RESET}")
    inicio, rotulo, nome_escolhido = escolher_inicio_bfs(
        region_idx, ing_idx, interativo=not args.sem_interativo
    )
    print(f"\n[BFS] {rotulo.capitalize()} escolhida: {RED}{nome_escolhido}{RESET}")
    distancias, _pais = bfs(graph, inicio)
    print(f"   Vértices alcançados: {len(distancias)}")

    camadas = defaultdict(list)
    for v, d in distancias.items():
        camadas[d].append(v)

    print("\n   Camadas BFS:")
    for d in sorted(camadas.keys()):
        print(f"\n   Distância {d} ({len(camadas[d])} nós):")
        for v in camadas[d][:10]:
            print(f"     {id_para_nome.get(v, f'Nó {v}')}")
    print(f"\n{BOLD}{GREEN} ### BFS concluído ###{RESET}")

    # ========================== Cliques ===========================
    print(f"\n{BOLD}{GREEN} ### Clique ###{RESET}")
    print("\n[Aviso] Esse grafo é BIPARTIDO (só existem arestas Região<->Ingrediente).")
    print("        Por isso todo clique máximo nele tem exatamente 2 elementos --")
    print("        não há grupos de 3+ pra analisar diretamente. Solução: projetar")
    print("        o grafo bipartido em dois grafos unipartidos, mantendo só os")
    print("        pares mais parecidos (top X%), e procurar cliques neles.")

    rodar_projecao(
        nome_projecao="Região-Região",
        descricao_clique="cada clique é um GRUPO DE REGIÕES cuja culinária é "
                         "mutuamente parecida (compartilham ingredientes com "
                         "pesos TF-IDF semelhantes).",
        lado_a_idx=region_idx,
        graph=graph,
        percentil_top=args.percentil,
        id_para_nome=id_para_nome,
    )

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


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--limiar", type=float, default=0.20,
                    help="limiar de Jaccard p/ ligar duas regiões no relatório (default 0.20)")
    ap.add_argument("--percentil", type=float, default=0.10,
                    help="fração do topo das similaridades de cosseno mantida (default 0.10)")
    ap.add_argument("--top-k", type=int, default=30,
                    help="tamanho da assinatura: top-k ingredientes por TF-IDF (default 30)")
    ap.add_argument("--regioes", default="",
                    help="regiões para desenhar a assinatura, separadas por vírgula "
                         "(default: france,italy,japan,china,mexico)")
    ap.add_argument("--sem-interativo", action="store_true",
                    help="pula os prompts do BFS (usa a primeira região) — útil p/ scripts")
    ap.add_argument("--sem-figuras", action="store_true",
                    help="não gerar as figuras do relatório (só o markdown)")
    args = ap.parse_args()

    regioes = [r.strip() for r in args.regioes.split(",") if r.strip()] or None

    # 1) Pipeline interativo do grupo (BFS + cliques no console).
    pipeline_interativo(args)

    # 2) Relatório consolidado (mesmos pesos), gravado em data/output/.
    print(f"\n\n{BOLD}{GREEN} ### Gerando relatório consolidado ###{RESET}")
    relatorio.gerar(limiar_jaccard=args.limiar, percentil_cosseno=args.percentil,
                    top_k=args.top_k, regioes=regioes, com_figuras=not args.sem_figuras)

    print(f"\n{BOLD}{CYAN}Relatório pronto.{RESET} O console acima é a exploração "
          "interativa (BFS + cliques); o relatório consolidado — com panorama, "
          "assinaturas, famílias (Jaccard e cosseno) e figuras embutidas — foi "
          "gravado em:")
    print(f"   {BOLD}data/output/relatorio.md{RESET}   (dados brutos em data/output/resultados.json)")
    print("\n=== Pipeline concluído ===")


if __name__ == "__main__":
    main()
