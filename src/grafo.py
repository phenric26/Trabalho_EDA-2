"""
Esse arquivo é o construtor do grafo através do dataset.

Em src/normalização/, é citado no README.md que existem dois problemas para serem resolvidos antes de construir o grafo,
    logo o grafo aqui já é construído com essas correções.

Solução para os dois problemas:
  Problema 1 (ingredientes onipresentes): filtra ingredientes que aparecem em
             mais de MAX_INGREDIENT_FREQ do total de receitas.
  Problema 2 (base desequilibrada): usa peso TF-IDF normalizado por região,
             não a contagem absoluta de co-ocorrências.

Estrutura do grafo:
  Vértices: Região  +  Ingrediente
  Arestas : Região <-> Ingrediente
  Peso    : TF-IDF  (diz o quão exclusivo esse ingrediente é para essa região)
"""

import pandas as pd
import math
import json
from collections import defaultdict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH     = BASE_DIR / "data" / "processed" / "culinarydb_arestas.csv" # Caminho para o dataset
MAX_INGREDIENT_FREQ = 0.20   # Problema 1: remove ingredientes em >20% das receitas
MIN_INGREDIENT_USES = 3      # remove ingredientes raros (<=2 usos globais)


print("Lendo arquivo .csv do dataset")
df = pd.read_csv(CSV_PATH)
df.columns = ["recipe_id", "ingredient", "region"]
df["ingredient"] = df["ingredient"].str.strip().str.lower()
df["region"]     = df["region"].str.strip().str.lower()

total_recipes = df["recipe_id"].nunique()
print(f"   {len(df):,} linhas | {total_recipes:,} receitas | "
      f"{df['region'].nunique()} regiões | {df['ingredient'].nunique()} ingredientes")


# Problema 1: filtrar ingredientes onipresentes
# Conta em quantas receitas cada ingrediente aparece (independente da região )
recipes_per_ingredient = df.groupby("ingredient")["recipe_id"].nunique()

ubiquitous_threshold = int(total_recipes * MAX_INGREDIENT_FREQ)
ubiquitous = set(recipes_per_ingredient[recipes_per_ingredient > ubiquitous_threshold].index)
rare        = set(recipes_per_ingredient[recipes_per_ingredient <= MIN_INGREDIENT_USES].index)
removed = ubiquitous | rare

print(f"\n Problema 1 — ingredientes removidos:")
print(f"   Onipresentes (>{MAX_INGREDIENT_FREQ*100:.0f}% das receitas): {len(ubiquitous)}")
for ing in sorted(ubiquitous, key=lambda x: -recipes_per_ingredient[x]):
    pct = recipes_per_ingredient[ing] / total_recipes * 100
    print(f"     - {ing}: {recipes_per_ingredient[ing]:,} receitas ({pct:.1f}%)")
print(f"   Raros (<={MIN_INGREDIENT_USES} usos): {len(rare)}")
print(f"   Total removido: {len(removed)} ingredientes")

df_clean = df[~df["ingredient"].isin(removed)].copy()
print(f"\n   Base após filtro: {len(df_clean):,} linhas | "
      f"{df_clean['ingredient'].nunique()} ingredientes restantes")

# Problema 2: peso TF-IDF normalizado por região 
#
#  Para cada par (região r, ingrediente i):
#
#  TF(r, i) = (receitas em r que usam i) / (total de receitas em r)
#             → frequência relativa dentro da região
#
#  IDF(i)   = log( N_regioes / qtd_regioes_que_usam_i )
#             → ingredientes usados em MUITAS regiões têm IDF baixo
#
#  peso(r, i) = TF(r, i) × IDF(i)
#
print("\n Problema 2 — calculando pesos TF-IDF")

# receitas únicas por região
total_recipes_per_region = df_clean.groupby("region")["recipe_id"].nunique()

# co-ocorrências: quantas receitas em cada região usam cada ingrediente
pair_recipes = (
    df_clean.groupby(["region", "ingredient"])["recipe_id"]
    .nunique()
    .reset_index()
    .rename(columns={"recipe_id": "count"})
)

# TF
pair_recipes["tf"] = pair_recipes.apply(
    lambda row: row["count"] / total_recipes_per_region[row["region"]], axis=1
)

# IDF: número de regiões distintas que usam cada ingrediente
regions_per_ingredient = df_clean.groupby("ingredient")["region"].nunique()
N = df_clean["region"].nunique()
idf = regions_per_ingredient.apply(lambda x: math.log(N / x) if x > 0 else 0)

pair_recipes["idf"]    = pair_recipes["ingredient"].map(idf)
pair_recipes["weight"] = pair_recipes["tf"] * pair_recipes["idf"]

print(f"   {len(pair_recipes):,} arestas com peso TF-IDF calculado")

# ── construção do grafo (listas de adjacência) ───────────────────────────────
print("\n Construindo grafo")

# Usei dicionários simples para não depender de bibliotecas de grafos

vertices_region     = sorted(df_clean["region"].unique())
vertices_ingredient = sorted(df_clean["ingredient"].unique())


# índices globais: regiões primeiro, depois ingredientes
region_idx = {r: i for i, r in enumerate(vertices_region)}
ing_idx    = {ing: i + len(vertices_region)
              for i, ing in enumerate(vertices_ingredient)}

graph = defaultdict(list)   # Lista de adjacências: {vertice: [(vizinho, peso), ...], ...}

for _, row in pair_recipes.iterrows():
    r_id   = region_idx[row["region"]]
    ing_id = ing_idx[row["ingredient"]]
    w      = round(row["weight"], 6)
    graph[r_id].append((ing_id, w))
    graph[ing_id].append((r_id, w))

total_vertices = len(vertices_region) + len(vertices_ingredient)
total_edges    = len(pair_recipes)

print(f"   Vértices: {total_vertices} ({len(vertices_region)} regiões + {len(vertices_ingredient)} ingredientes)")
print(f"   Arestas:  {total_edges:,} (bidirecionais → {total_edges*2:,} entradas na lista)")

# salvar grafo e metadados para análises futuras (e.g. centralidade, comunidades, etc)
output_edges  = BASE_DIR / "data" / "processed" / "arestas_com_peso.csv"
output_meta   = BASE_DIR / "data" / "processed" / "metadados_grafo.json"

os.makedirs(os.path.expanduser("~/Trabalho_EDA-2/data/processed"), exist_ok=True)

# CSV de arestas (pronto para carregar em qualquer outro módulo)
pair_recipes[["region", "ingredient", "count", "tf", "idf", "weight"]].to_csv(
    output_edges, index=False
)

# metadados do grafo
meta = {
    "total_vertices": total_vertices,
    "total_regions":  len(vertices_region),
    "total_ingredients": len(vertices_ingredient),
    "total_edges": total_edges,
    "removed_ubiquitous": sorted(ubiquitous),
    "max_ingredient_freq_threshold": MAX_INGREDIENT_FREQ,
    "min_ingredient_uses_threshold": MIN_INGREDIENT_USES,
    "regions": vertices_region,
    "top10_edges_by_weight": (
        pair_recipes.nlargest(10, "weight")[["region","ingredient","weight"]]
        .to_dict(orient="records")
    )
}
with open(output_meta, "w") as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print(f"\n Dados salvos:")
print(f"   {output_edges}")
print(f"   {output_meta}")

# top ingredientes por região 
print("\n Top 5 ingredientes por peso TF-IDF (amostra de regiões):")
sample_regions = ["usa", "italy", "japan", "mexico", "india"]
for reg in sample_regions:
    if reg not in region_idx:
        continue
    top = (pair_recipes[pair_recipes["region"] == reg]
           .nlargest(5, "weight")[["ingredient", "weight"]])
    print(f"\n  {reg.upper()}:")
    for _, r in top.iterrows():
        print(f"    {r['ingredient']:<30} tfidf={r['weight']:.4f}")