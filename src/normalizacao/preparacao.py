import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

caminho_01 = BASE_DIR / 'data' / 'raw' / '01_Recipe_Details.csv'
caminho_04 = BASE_DIR / 'data' / 'raw' / '04_Recipe-Ingredients_Aliases.csv'
caminho_saida = BASE_DIR / 'data' / 'processed' / 'culinarydb_arestas.csv'

print("Carregando o CulinaryDB...")
df_receitas = pd.read_csv(caminho_01)
df_ingredientes = pd.read_csv(caminho_04)


print("Fazendo o Join entre Receitas, Regiões e Ingredientes...")

df_grafo = pd.merge(df_ingredientes[['Recipe ID', 'Aliased Ingredient Name']],
                    df_receitas[['Recipe ID', 'Cuisine']],
                    on='Recipe ID',
                    how='inner')

print("Aplicando limpeza e padronização dos Nós...")

df_grafo = df_grafo.dropna(subset=['Cuisine', 'Aliased Ingredient Name'])


df_grafo['Cuisine'] = df_grafo['Cuisine'].str.lower().str.strip()
df_grafo['Aliased Ingredient Name'] = df_grafo['Aliased Ingredient Name'].str.lower().str.strip()


df_grafo = df_grafo.drop_duplicates(subset=['Recipe ID', 'Aliased Ingredient Name', 'Cuisine'])


caminho_saida.parent.mkdir(parents=True, exist_ok=True)
df_grafo.to_csv(caminho_saida, index=False)

print(f"Sucesso! Arquivo base para o Grafo salvo em: {caminho_saida}")
print(f"Total de conexões (Arestas) geradas: {len(df_grafo)}")
