# Relatório de Análise — Grafo Culinário (CulinaryDB)

*Documento gerado automaticamente em 22/06/2026.*

| | |
|---|---|
| **Base de dados** | CulinaryDB |
| **Modelagem** | grafo bipartido região ↔ ingrediente |
| **Peso das arestas** | TF-IDF (frequência regional normalizada) |
| **Algoritmos** | BFS, Bron–Kerbosch, similaridade de Jaccard e de cosseno |
| **Limiar de Jaccard** | 0.2 |
| **Percentil do cosseno** | 10% |
| **Assinatura regional** | top-30 ingredientes por TF-IDF |

---

## Sumário

1. [Panorama do grafo bipartido](#1-panorama-do-grafo-bipartido)
2. [Assinatura regional por TF-IDF](#2-assinatura-regional-por-tf-idf)
3. [Conectividade e distâncias (fila e BFS)](#3-conectividade-e-distâncias-fila-e-bfs)
4. [Famílias de regiões (Bron–Kerbosch sobre a similaridade)](#4-famílias-de-regiões-bronkerbosch-sobre-a-similaridade)
5. [Famílias de ingredientes (projeção ingrediente-ingrediente)](#5-famílias-de-ingredientes-projeção-ingrediente-ingrediente)
6. [Sensibilidade ao limiar](#6-sensibilidade-ao-limiar)

---

## 1. Panorama do grafo bipartido

- **26 regiões**, **666 ingredientes**, **7875 arestas** região↔ingrediente.
- Densidade bipartida: **45.5%**.
- Grau por região: min **49**, médio **302.9**, máx **623**.

| região | ingrediente | TF-IDF |
|---|---|---|
| indian subcontinent | asafoetida | 0.3256 |
| indian subcontinent | mustard oil | 0.317 |
| indian subcontinent | ghee | 0.317 |
| greece | cheese feta | 0.1931 |
| misc.: central america | burrito | 0.1832 |
| korea | sesame | 0.1639 |
| misc.: belgian | cheese gruyere | 0.1572 |
| japan | sake | 0.1547 |
| indian subcontinent | curry leaf | 0.1515 |
| japan | bonito | 0.1462 |

![Panorama bipartido Região ↔ Ingrediente](panorama_bipartido.png)

![Arestas de maior peso TF-IDF](top_arestas.png)

## 2. Assinatura regional por TF-IDF

- **africa**: couscou, chickpea, harissa, saffron, cumin, turmeric
- **australia & nz**: cheese feta, cheese parmesan, oat, pasta, salad dressing, artichoke
- **british isles**: buttermilk, whiskey, currant, baking soda, oat, rutabaga
- **canada**: oat, tart shell, cocoa powder, flax seed, blueberry, barbeque sauce
- **caribbean**: plantain french, scotch, rum, lime, mango, coconut milk
- **china**: sesame, soy sauce, hoisin sauce, chinese five spice, oyster, water chestnut
- **dach countries**: sauerkraut, caraway, flour, anise, veal, cocoa powder
- **eastern europe**: sauerkraut, dill, beet, caraway, poppy seed, cheese cottage
- **france**: cheese gruyere, chocolate, cocoa butter, shallot, baguette, brandy cognac
- **greece**: cheese feta, feta  cheese, phyllo, bread pita, oregano, dill
- **indian subcontinent**: asafoetida, ghee, mustard oil, curry leaf, sunflower, garam masala
- **italy**: parmesan  cheese, cheese ricotta, cheese parmesan, pasta, mozzarella  cheese, lasagna
- **japan**: sake, bonito, kombu, miso, sesame, wasabi
- **korea**: sesame, soy sauce, daikon, scallion, kombu, tofu
- **mexico**: taco, tortilla, enchilada, tortilla chip, tequila, oregano mexican
- **middle east**: bulgur, tahini, chickpea, bread pita, couscou, pomegranate
- **misc.: belgian**: cheese gruyere, endive, whiskey, prosciutto, flour, beer
- **misc.: central america**: burrito, oregano mexican, chayote, pie, tequila, cilantro
- **misc.: dutch**: treacle, meatloaf, currant, apple, flour, pie
- **misc.: portugal**: pimenta, bean kidney, kale, port wine, spanish  sage, paprika
- **scandinavia**: lingonberry, herring, cardamom, dill, bread rye, flour
- **south america**: cilantro, corn, lime, plantain french, milk condensed, tapioca
- **south east asia**: lemongras, fish, peanut, bean mung, vermicelli, coconut milk
- **spain**: saffron, spanish  sage, pimiento, chickpea, paprika, baguette
- **thailand**: lemongras, coconut milk, kaffir beer, peanut, fish, peanut butter
- **usa**: cajun seasoning, pecan, buttermilk, cheddar  cheese, corn, chocolate

![Ingredientes-assinatura de france](regiao_france.png)

![Ingredientes-assinatura de italy](regiao_italy.png)

![Ingredientes-assinatura de japan](regiao_japan.png)

![Ingredientes-assinatura de china](regiao_china.png)

![Ingredientes-assinatura de mexico](regiao_mexico.png)


## 3. Conectividade e distâncias (fila e BFS)

- Grafo **conexo**: alcançam-se 692/692 vértices.
- **Diâmetro região↔região: 2 arestas** (2 = compartilham um ingrediente).

**Ingrediente-ponte entre cozinhas distintas** (caminho mínimo BFS, desempate por TF-IDF):

| de | para | distância | ingrediente(s)-ponte |
|---|---|---|---|
| japan | mexico | 2 | sesame |
| italy | japan | 2 | parmesan  cheese |
| indian subcontinent | france | 2 | sunflower |
| scandinavia | thailand | 2 | cardamom |

## 4. Famílias de regiões (Bron–Kerbosch sobre a similaridade)

- **Jaccard** (assinatura top-30), limiar 0.2: **21 arestas**.
- **Cosseno** (vetor TF-IDF completo), percentil 10% → limiar 0.3513: **32 arestas**.
- Concordância: acordo total 92.3%, Jaccard-de-arestas **35.9%**.

![Heatmap de Jaccard + famílias culinárias (limiar 0.2)](similaridade_regioes.png)

**Famílias por Jaccard:**
  - (4) china, korea, south east asia, thailand
  - (3) british isles, dach countries, misc.: dutch
  - (3) china, japan, korea
  - (3) dach countries, eastern europe, scandinavia
  - (2) africa, middle east
  - (2) australia & nz, greece
  - (2) canada, usa
  - (2) caribbean, south america
  - (2) greece, italy
  - (2) greece, middle east
  - (2) mexico, misc.: central america

**Famílias por Cosseno:**
  - (5) australia & nz, british isles, canada, france, usa
  - (4) australia & nz, france, italy, usa
  - (3) china, south east asia, thailand
  - (3) china, japan, korea
  - (3) australia & nz, south america, usa
  - (3) caribbean, south america, usa
  - (2) africa, spain
  - (2) africa, middle east
  - (2) dach countries, eastern europe
  - (2) australia & nz, greece
  - (2) greece, middle east
  - (2) france, misc.: belgian
  - (2) british isles, misc.: dutch
  - (2) eastern europe, scandinavia
  - (2) eastern europe, usa

**Famílias idênticas nas duas lentes (robustas):**
  - (2) greece, middle east
  - (2) australia & nz, greece
  - (2) africa, middle east
  - (3) china, japan, korea

- Clique asiático *china/korea/south east asia/thailand*: Jaccard = sim, Cosseno = não.

## 5. Famílias de ingredientes (projeção ingrediente-ingrediente)

- Percentil 1% → limiar 0.8459; **473 cliques**, 151 com >2 elementos, maior com **32**.
  - (32) amchoor, asafetida, asafoetida, bay laurel, bean cluster, bitter gourd, bread wheaten, capsicum (+24)
  - (31) amchoor, asafetida, asafoetida, bay laurel, bean cluster, bitter gourd, bread wheaten, capsicum (+23)
  - (30) amchoor, asafetida, asafoetida, bay laurel, bean cluster, bitter gourd, bottle gourd, bread wheaten (+22)
  - (30) amchoor, asafetida, asafoetida, bay laurel, bean cluster, bitter gourd, bread wheaten, capsicum (+22)
  - (18) cheese provolone, cheese ricotta, cheese romano, curd, cuttlefish, fettuccine, lady finger, lasagna (+10)

## 6. Sensibilidade ao limiar

| método | parâmetro | arestas | famílias | maior clique |
|---|---|---|---|---|
| Jaccard | limiar 0.15 | 34 | 15 | 4 |
| Jaccard | limiar 0.2 | 21 | 11 | 4 |
| Jaccard | limiar 0.25 | 7 | 5 | 3 |
| Jaccard | limiar 0.3 | 5 | 5 | 2 |
| Cosseno | 5% (lim 0.4297) | 16 | 13 | 3 |
| Cosseno | 10% (lim 0.3513) | 32 | 15 | 5 |
| Cosseno | 15% (lim 0.2984) | 48 | 21 | 5 |
| Cosseno | 20% (lim 0.2631) | 65 | 20 | 6 |

