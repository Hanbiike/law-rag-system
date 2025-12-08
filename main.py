from searchers import text_search
import asyncio
searcher = text_search.ProLawRAGSearch(top_k=5, n_llm_questions=5)
# asyncio.run(searcher.get_response("Какие права имеет работник при увольнении по сокращению штатов?", type='pro', lang='ru'))
asyncio.run(searcher.get_response("Мени жумуштан мыйзамсыз чыгарса кандай укуктарым бар?", type='pro', lang='kg'))