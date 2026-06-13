import spacy
import re
import pandas as pd 
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

caminho_entrada = BASE_DIR / 'data' / 'processed' / '3A2M_entidades_processadas.csv'
caminho_saida = BASE_DIR / 'data' / 'processed' / '3A2M_pronto_para_grafos.csv'

nlp = spacy.load("en_core_web_sm")

stopwords_culinaries = {"cup", "tablespoon", "teaspoon", "ounce", "pound", "gram", "kg", 
    "pinch", "taste", "minute", "hour", "degree", "f", "c", "add", "mix", "stir",
    "mixture", "pan", "pour", "ingredient", "inch", "combine", "cool", 
    "oven", "piece", "set", "aside", "like", "use", "direction", "package"}

for word in stopwords_culinaries:
    nlp.vocab[word].is_stop = True 


def processar_texto_receita(texto):

    if not isinstance(texto, str):
        return []

    texto_limpo = re.sub(r'[^a-zA-Z\s]', ' ', texto)
    texto_limpo = texto_limpo.lower()

    nlp.max_length = 2000000
    doc = nlp(texto_limpo)

    tokens_uteis = []

    for token in doc:

        lemma = token.lemma_

        if not token.is_punct and not token.is_space and len(token.text) > 1:
            if not token.is_stop and lemma not in stopwords_culinaries:
                tokens_uteis.append(lemma)

    return tokens_uteis

exemplo_direcao = "Preheat oven to 350 degrees F. Mix 2 cups of flour and chopped tomatoes."
print("Original:", exemplo_direcao)
print("Processado:", processar_texto_receita(exemplo_direcao))

print(f"Carregando {caminho_entrada}...")

df = pd.read_csv(caminho_entrada, nrows=200000)
#df = pd.read_csv(caminho_entrada)

print("Processando a coluna directions (Isso pode demorar bastante!)...")
df['directions_processadas'] = df['directions'].apply(processar_texto_receita)

# Salvar o resultado
print(f"Salvando dataframe final em {caminho_saida}...")
df.to_csv(caminho_saida, index=False)
print("Pipeline de NLP concluído!")
