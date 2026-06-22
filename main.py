"""Entrypoint do projeto: gera o relatório de análise do grafo culinário.

Roda todos os algoritmos do grupo (grafo TF-IDF, BFS/fila, Bron-Kerbosch,
Jaccard e cosseno) para os pesos escolhidos e grava o resultado consolidado
em data/output/relatorio.md (com as figuras embutidas).

Exemplos:
    uv run python3 main.py
    uv run python3 main.py --limiar 0.25 --percentil 0.05 --top-k 40
    uv run python3 main.py --sem-figuras
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from relatorio import gerar  # noqa: E402  (precisa do sys.path acima)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limiar", type=float, default=0.20,
                    help="limiar de Jaccard p/ ligar duas regiões (default 0.20)")
    ap.add_argument("--percentil", type=float, default=0.10,
                    help="fração do topo das similaridades de cosseno mantida (default 0.10)")
    ap.add_argument("--top-k", type=int, default=30,
                    help="tamanho da assinatura: top-k ingredientes por TF-IDF (default 30)")
    ap.add_argument("--regioes", default="",
                    help="regiões para desenhar a assinatura, separadas por vírgula "
                         "(default: france,italy,japan,china,mexico)")
    ap.add_argument("--sem-figuras", action="store_true",
                    help="não gerar as figuras (só o markdown)")
    args = ap.parse_args()

    regioes = [r.strip() for r in args.regioes.split(",") if r.strip()] or None

    gerar(limiar_jaccard=args.limiar, percentil_cosseno=args.percentil,
          top_k=args.top_k, regioes=regioes, com_figuras=not args.sem_figuras)


if __name__ == "__main__":
    main()
