from pymilvus import MilvusClient, DataType
import numpy as np
import json

client = MilvusClient("milvus_law_rag.db")

# если коллекция уже есть – удаляем
if client.has_collection(collection_name="law_collection_kg"):
    client.drop_collection(collection_name="law_collection_kg")

if client.has_collection(collection_name="law_collection"):
    client.drop_collection(collection_name="law_collection")

# создаём коллекцию только с векторным полем (остальное пойдёт как dynamic fields)
client.create_collection(
    collection_name="law_collection",
    dimension=768,          # размер вектора
    metric_type="COSINE",   # или "L2" – как у тебя обучены эмбеддинги
)

client.create_collection(
    collection_name="law_collection_kg",
    dimension=768,          # размер вектора
    metric_type="COSINE",   # или "L2" – как у тебя обучены эмбеддинги
)

# загрузка данных из JSONL
with open("law_rag_db.json", "r", encoding="utf-8") as f:
    raw = f.readlines()

data = []
for line in raw:
    # если последняя строка то только убираем 1 символ
    if line == raw[-1]:
        line = line[:-1]
    else:
        line = line[:-2]  # убираем символ переноса строки
    json_obj = json.loads(line)
    json_obj['id'] = int(json_obj['id'])
    json_obj['vector'] = np.array(json.loads(json_obj['vector']), dtype=np.float32)
    data.append({"id": json_obj['id'], "vector": json_obj['vector'], "source_doc": json_obj['source_doc'], "section": json_obj['section'], "chapter": json_obj['chapter'], "article_title": json_obj['article_title'], "article_text": json_obj['article_text']})

client.insert(
    collection_name="law_collection",
    data=data,
)

# загрузка данных из JSONL
with open("law_rag_db_kg.json", "r", encoding="utf-8") as f:
    raw = f.readlines()

data = []
for line in raw:
    # если последняя строка то только убираем 1 символ
    if line == raw[-1]:
        line = line[:-1]
    else:
        line = line[:-2]  # убираем символ переноса строки
    json_obj = json.loads(line)
    json_obj['id'] = int(json_obj['id'])
    json_obj['vector'] = np.array(json.loads(json_obj['vector']), dtype=np.float32)
    data.append({"id": json_obj['id'], "vector": json_obj['vector'], "source_doc": json_obj['source_doc'], "section": json_obj['section'], "chapter": json_obj['chapter'], "article_title": json_obj['article_title'], "article_text": json_obj['article_text']})

client.insert(
    collection_name="law_collection_kg",
    data=data,
)

print(client.describe_collection("law_collection"))
print(client.describe_collection("law_collection_kg"))

client.load_collection("law_collection")
client.load_collection("law_collection_kg")

# Посмотрим первыйи  второй векторы
res = client.query(
    collection_name="law_collection",
    output_fields=["id", "vector", "source_doc", "article_title"],
    limit=1,
)

print(res)