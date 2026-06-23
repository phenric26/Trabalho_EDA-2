# Processamento de linguagem natural com grafos

Este repositório é destinado ao trabalho da disciplina Estruturas de Dados 2 da Universidade de Brasília (UnB). O trabalho consiste na implementação de um sistema de análise de dados baseado em grafos, utilizando técnicas de coocorrência, projeção por similaridade, busca em largura (BFS) e detecção de cliques máximos (Bron-Kerbosch).

## Participantes

|              Nome           |  Matrícula |
|-----------------------------|------------|
| José Joaquim da Silva Neto          | 232027510 |
| Marcus Vinicius Rezende dos Santos  | 232038335 |
| Pedro Henrique Gomes                | 232030041 |
| Joao Gabriel Milhomem de Brito      | 221022005 |
| Leonardo Fachinello Bonetti         | 221022060 |



## Objetivo
Implementar um sistema de análise textual baseado em grafos. Dada uma coleção de documentos, construa um grafo de coocorrência de palavras (ou frases ou sentenças), onde cada vértice representa uma palavra (ou frase ou sentença) e cada aresta representa a ocorrência conjunta de duas palavras (ou frases ou sentenças) no mesmo documento. Utilize pesos nas arestas, aplique técnicas de filtragem e identifique grupos de palavras relacionadas no grafo. 

O projeto utiliza o dataset **CulinaryDB**, construindo um **grafo bipartido** onde:

- Um conjunto de vértices representa **regiões culinárias**;
- O outro conjunto de vértices representa **ingredientes**;
- As arestas conectam região e ingrediente sempre que aquele ingrediente é utilizado naquela região, com peso dado pela **frequência TF-IDF normalizada**.

A partir desse grafo bipartido, o sistema realiza três tipos de análise:

1. **Busca em Largura (BFS)** — percorre o grafo a partir de um vértice escolhido pelo usuário (região ou ingrediente), agrupando os demais vértices alcançados por distância (camadas).
2. **Projeção por similaridade de cosseno** — como o grafo bipartido não permite cliques de tamanho maior que 2 (não há arestas dentro do mesmo lado), o sistema projeta o grafo original em dois grafos unipartidos:
   - **Região-Região**: aresta entre duas regiões se a culinária de ambas for suficientemente parecida (uso semelhante de ingredientes, ponderado por TF-IDF).
   - **Ingrediente-Ingrediente**: aresta entre dois ingredientes se ambos tiverem padrão de uso regional semelhante (possível "assinatura" de cozinha).

3. **Busca de cliques máximos (Bron-Kerbosch)** — aplicada sobre os grafos projetados, identificando grupos de regiões ou ingredientes mutuamente relacionados entre si.

## Problema

A culinária de diferentes regiões do mundo pode ser caracterizada pelos ingredientes utilizados em suas receitas. Entretanto, identificar relações entre cozinhas distintas ou ingredientes culturalmente associados não é trivial quando analisamos milhares de receitas individualmente.

Este trabalho propõe modelar essas relações por meio de grafos, utilizando técnicas de Processamento de Linguagem Natural (PLN) para extrair, normalizar e ponderar ingredientes a partir de dados textuais do dataset CulinaryDB.

A partir dessa modelagem, buscamos responder perguntas como:

- Quais regiões possuem culinárias semelhantes?
- Quais ingredientes caracterizam uma determinada região?
- Existem grupos de regiões fortemente relacionadas?
- Existem ingredientes que aparecem em padrões de uso semelhantes?

## Aplicação de PLN

Embora o foco principal do trabalho seja a modelagem em grafos, técnicas de Processamento de Linguagem Natural foram empregadas durante a preparação dos dados.

As etapas incluem:

- Normalização textual dos ingredientes;
- Remoção de inconsistências e duplicidades;
- Tratamento de ruídos linguísticos;
- Representação vetorial utilizando TF-IDF;
- Construção das relações semânticas entre regiões e ingredientes.

Dessa forma, os dados textuais são transformados em uma estrutura de grafo adequada para análise.


## Decisões Arquiteturais e Estruturas de Dados

* **Representação do Grafo (Lista de Adjacências):** O grafo bipartido (Região ↔ Ingrediente) e suas projeções foram implementados utilizando dicionários/listas de adjacência.
  * *Justificativa Técnica:* Como a relação entre culinárias e ingredientes mundiais é esparsa (nem toda região usa todos os ingredientes), uma Matriz de Adjacência desperdiçaria memória de forma ineficiente. A lista de adjacência otimiza o uso de memória para $O(V + E)$ e permite iterações extremamente rápidas sobre os vizinhos de um nó.
* **Estrutura de Dados Adicional (Fila/Queue):** Implementada de forma modular (`src/fila.py`) e utilizada como motor principal do algoritmo de Busca em Largura (BFS).
  * *Justificativa Técnica:* A estrutura clássica de Fila (FIFO - *First In, First Out*) é o requisito matemático necessário para garantir a correta varredura por camadas (níveis de distância) da BFS. Ela garante operações de enfileirar e desenfileirar em tempo $O(1)$, mantendo a complexidade total da busca eficiente.
* **Modelagem de Pesos (TF-IDF):** As arestas do grafo não indicam apenas a presença bruta de um ingrediente, mas o seu peso cultural relativo calculado via TF-IDF (*Term Frequency-Inverse Document Frequency*). Isso resolve o problema de ingredientes super-comuns (como "sal" e "água") dominarem as similaridades, destacando os ingredientes que são verdadeiras assinaturas regionais.
* **Complexidade dos Algoritmos Implementados:**
  * **BFS:** $O(V + E)$, garantindo percurso rápido e controle exato de camadas de separação.
  * **Similaridade de Cosseno:** Aplicada na projeção para criar o grafo unipartido, calculando a distância vetorial baseada em pesos de forma eficiente.
  * **Bron-Kerbosch (Cliques Máximos):** Algoritmo de *backtracking* otimizado utilizado nos grafos unipartidos para encontrar componentes completa e fortemente conexos ("panelinhas" culturais incontestáveis).

## Estrutura do repositório

```
.
├── main.py                       # entrypoint: pipeline interativo (BFS + cliques) + gera o relatório
├── visualizacao.py               # desenho do grafo bipartido (só matplotlib/networkx)
├── visualizacao_similaridade.py  # desenho do heatmap + grafo de famílias de regiões
├── gerar_visualizacao_bfs.py     # exporta a visualização do BFS
├── grafo_culinario.html          # visualização interativa (D3.js) do grafo
├── data/
│   ├── processed/
│   │   ├── arestas_com_peso.csv
│   │   ├── culinarydb_arestas.csv
│   │   └── metadados_grafo.json
│   └── output/                   # artefatos gerados (relatorio.md, resultados.json, PNGs)
├── slides/
├── src/
│   ├── normalizacao/
│   │   ├── entidades.py
│   │   ├── nlp.py
│   │   ├── preparacao.py
│   │   ├── README.md
│   │   └── validacao.py
│   ├── fila/                     # estrutura de dados Fila + BFS (pacote)
│   │   ├── __init__.py
│   │   ├── fila.py               # Fila (FIFO) sobre lista encadeada
│   │   └── bfs.py                # Busca em Largura
│   ├── grafo.py                  # construção do grafo bipartido TF-IDF
│   ├── clique.py                 # Bron-Kerbosch (cliques máximos)
│   ├── cosseno.py                # similaridade de cosseno + projeção do grafo
│   ├── similaridade.py           # Jaccard entre assinaturas de regiões
│   └── relatorio.py              # orquestra todas as peças e gera o relatório
├── testes/
│   └── teste_bfs.py
├── .gitignore
├── pyproject.toml
├── README.md
├── requirements.txt
└── uv.lock
```

> As bibliotecas `matplotlib`/`networkx` são usadas **apenas para desenhar**. Toda
> medida (TF-IDF, BFS, cliques, Jaccard, cosseno) é calculada pelo código do grupo.

## Como executar

As dependências de desenho não ficam no Python global; use `uv run`:

```bash
uv run python3 main.py                                   # interativo + relatório (defaults)
uv run python3 main.py --limiar 0.25 --percentil 0.05 --top-k 40
uv run python3 main.py --sem-interativo                  # pula os prompts do BFS
```

O programa solicita interativamente:
1. O tipo de vértice inicial do BFS (região ou ingrediente);
2. O vértice específico dentro do tipo escolhido.

Em seguida, o pipeline executa:
- BFS a partir do vértice escolhido, exibindo as camadas de distância;
- Projeção Região-Região e busca de cliques máximos (Bron-Kerbosch);
- Projeção Ingrediente-Ingrediente e busca de cliques máximos.

Ao final, gera o **relatório consolidado** em `data/output/relatorio.md` (com as
figuras embutidas) e os dados brutos em `data/output/resultados.json`.
