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

## Estrutura do repositório

```
.
├── main.py
├── analises/
│   ├── data/
│   │   └── output/
│   │       ├── panorama_bipartido.png
│   │       ├── regiao_italy.png
│   │       ├── similaridade_regioes.png
│   │       └── top_arestas.png 
│   ├── gerar_visualizacao_bfs.py
│   ├── visualizacao_similaridade.py
│   └── visualizacao.py 
├── data/
│   └── processed/
│       ├── arestas_com_peso.csv
│       ├── culinarydb_arestas.csv
│       └── metadados_grafo.json
├── slides/
│   └──             
├── src/
│   ├── normalizacao/
│   │   ├── entidades.py
│   │   ├── nlp.py
│   │   ├── preparacao.py
│   │   ├── README.md
│   │   └── validacao.py
│   ├── bfs.py          
│   ├── clique.py          
│   ├── fila.py          
│   ├── grafo.py             
│   └── similaridade.py
├── .gitignore
├── main.py  
├── pyproject.toml        
├── README.md
├── requirements.txt
└── uv.lock
```

## Como executar

```bash
python main.py
```

O programa solicitará interativamente:
1. O tipo de vértice inicial do BFS (região ou ingrediente);
2. O vértice específico dentro do tipo escolhido.

Em seguida, o pipeline executa automaticamente:
- BFS a partir do vértice escolhido, exibindo as camadas de distância;
- Projeção Região-Região e busca de cliques máximos;
- Projeção Ingrediente-Ingrediente e busca de cliques máximos.tuamente relacionados entre si.