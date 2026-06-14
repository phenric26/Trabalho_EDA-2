def bron_kerbosch(R, P, X, grafo, cliques):
    """
    Algoritmo clássico para encontrar Cliques Máximos.
    R: Clique atual em construção.
    P: Vértices candidatos.
    X: Vértices já processados.
    """
    if not P and not X:
        cliques.append(R)
        return

    for vertice in list(P):
        vizinhos = grafo[vertice]
        
        bron_kerbosch(
            R | {vertice},
            P & vizinhos,
            X & vizinhos,
            grafo,
            cliques
        )
        P.remove(vertice)
        X.add(vertice)

# --- MOCK DE TESTE ---
grafo_teste = {
    'A': {'B', 'C'},
    'B': {'A', 'C'},
    'C': {'A', 'B', 'D'},
    'D': {'C'}
}

cliques_encontrados = []
R = set()
P = set(grafo_teste.keys())
X = set()

bron_kerbosch(R, P, X, grafo_teste, cliques_encontrados)

print("Cliques máximos encontrados:", cliques_encontrados)
