### 📊 Resultados da Normalização 

A fase de normalização de dados foi concluída. O arquivo base para alimentar o Grafo é o `data/processed/culinarydb_arestas.csv`. Ele contém as conexões limpas e bidimensionais entre o País (Região) e o Ingrediente Padronizado.

#### Raio-X da Base de Dados (Validação)

```text
=== 1. O TAMANHO DO SEU FUTURO GRAFO ===
Total de Arestas (Conexões): 414.779
Total de Vértices de Região: 26
Total de Vértices de Ingrediente: 865
Total de Receitas Base: 45.749

=== 2. OS SUPER-HUBS (Ingredientes mais comuns) ===
- salt: 18.745 conexões (presente em 41.0% das receitas)
- pepper: 16.065 conexões (presente em 35.1% das receitas)
- garlic: 15.995 conexões (presente em 35.0% das receitas)
- onion: 13.877 conexões (presente em 30.3% das receitas)
- olive: 13.476 conexões (presente em 29.5% das receitas)

=== 3. AS MAIORES REGIÕES (Por volume de receitas) ===
- usa: 16.106 receitas base
- italy: 7.502 receitas base
- indian subcontinent: 4.057 receitas base
- mexico: 3.138 receitas base
- france: 2.701 receitas base

=== 4. SAÚDE E RUÍDO DO GRAFO ===
Ingredientes Raros (usados <= 2 vezes): 160 (18.5% de todos os ingredientes)
```

## Problema 1: 

Ingredientes como Sal, Água, Alho e Cebola aparecem em quase 40% de todas as receitas do mundo. Se remover, o algoritmo de grafos vai concluir que o Japão e o México são culinárias "irmãs" simplesmente porque ambos usam água e sal.


A Solução (acho que resolve): Antes de adicionar os nós ao grafo, criar um limite que delete ingredientes que apareçam demais, como por exemplo 20% do total de receitas


## Problema 2: 
A base de dados é desequilibrada. Os EUA possuem mais de 16.000 receitas mapeadas, enquanto países como a França possuem apenas 2.700. Se criar o peso da aresta somando a quantidade absoluta de ingredientes em comum, os EUA vão parecer conectados a todos os outros países apenas por terem um grande volume de dados. 
