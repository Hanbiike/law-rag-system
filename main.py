from searchers import search
import asyncio
import base64

searcher = search.ProLawRAGSearch(top_k=1, n_llm_questions=2)
# asyncio.run(searcher.get_response("Какие права имеет работник при увольнении по сокращению штатов?", type='pro', lang='ru'))
# asyncio.run(searcher.get_response("Мени жумуштан мыйзамсыз чыгарса кандай укуктарым бар?", type='pro', lang='kg'))

with open("pril-9-regl.pdf", "rb") as f:
    data = f.read()

base64_string = base64.b64encode(data).decode("utf-8")

asyncio.run(searcher.get_response_from_doc(
    query="Законен ли данный документ?",
    document_base64=base64_string,
    type='pro',
    lang='ru'
))