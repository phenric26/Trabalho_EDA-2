import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
caminho_csv = BASE_DIR / 'data' / 'processed' / 'culinarydb_arestas.csv'

print("Carregando lista de arestas...\n")
df = pd.read_csv(caminho_csv)

total_arestas = len(df)
total_receitas = df['Recipe ID'].nunique()
regioes_unicas = df['Cuisine'].nunique()
ingredientes_unicos = df['Aliased Ingredient Name'].nunique()

print("=== 1. O TAMANHO DO SEU FUTURO GRAFO ===")
print(f"Total de Arestas (Conexões): {total_arestas}")
print(f"Total de Vértices de Região: {regioes_unicas}")
print(f"Total de Vértices de Ingrediente: {ingredientes_unicos}")
print(f"Total de Receitas que geraram isso: {total_receitas}\n")

top_ingredientes = df['Aliased Ingredient Name'].value_counts().head(10)
print("=== 2. OS SUPER-HUBS (Ingredientes mais comuns) ===")
for ing, contagem in top_ingredientes.items():
    porcentagem = (contagem / total_receitas) * 100
    print(f"- {ing}: {contagem} conexões (presente em {porcentagem:.1f}% das receitas)")

# 3. VERIFICAÇÃO DE DISTRIBUIÇÃO REGIONAL
top_regioes = df.drop_duplicates(subset=['Recipe ID', 'Cuisine'])['Cuisine'].value_counts().head(5)
print("\n=== 3. AS MAIORES REGIÕES (Por volume de receitas) ===")
for regiao, contagem in top_regioes.items():
    print(f"- {regiao}: {contagem} receitas base")

# 4. A SAÚDE DO GRAFO (Nós raros)
contagem_ingredientes = df['Aliased Ingredient Name'].value_counts()
ingredientes_raros = contagem_ingredientes[contagem_ingredientes <= 2].count()
percentual_raros = (ingredientes_raros / ingredientes_unicos) * 100

print("\n=== 4. SAÚDE E RUÍDO DO GRAFO ===")
print(f"Ingredientes Raros (usados <= 2 vezes): {ingredientes_raros} ({percentual_raros:.1f}% de todos os ingredientes)")

