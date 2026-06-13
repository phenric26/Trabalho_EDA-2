import pandas as pd 
import ast
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent.parent.parent

caminho_3a2m = BASE_DIR / 'data' / 'raw' / '3A2M.csv'
caminho_aliases = BASE_DIR / 'data' / 'raw' / '04_Recipe-Ingredients_Aliases.csv'

caminho_saida = BASE_DIR / 'data' / 'processed' / '3A2M_entidades_processadas.csv'

print("Carregando os datasets")

df_3a2m = pd.read_csv(caminho_3a2m)
df_aliases = pd.read_csv(caminho_aliases)


dict_aliases = dict(zip(df_aliases['Original Ingredient Name'].str.lower(), 
                        df_aliases['Aliased Ingredient Name'].str.lower()))


def normalizar_ingrediantes(linha_ner):
    
    try:
        ingredientes = ast.literal_eval(linha_ner)

    except:
        return []


    ingredientes_padronizados = []

    for ing in ingredientes:
        ing_limpo = str(ing).strip().lower()

        ing_padrao = dict_aliases.get(ing_limpo, ing_limpo)

        ingredientes_padronizados.append(ing_padrao)

    return list(set(ingredientes_padronizados))


print("Normalizando ingredientes")

df_3a2m['NER_padronizado'] = df_3a2m['NER'].apply(normalizar_ingrediantes)

print(df_3a2m[['NER', 'NER_padronizado']].head())

print(f"Salvando dados processados em {caminho_saida}...")

caminho_saida.parent.mkdir(parents=True, exist_ok=True) 

df_3a2m.to_csv(caminho_saida, index=False)
print("Concluído!")
