# RAG evaluation results

2026-10-13 · 70 questions · 16 chunks from eval/corpus · backend: sqlite

| Retrieval | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---|---|---|---|
| vector only | 0.871 | 0.957 | 1.000 | 0.923 |
| hybrid (vector + BM25, RRF) | 0.900 | 0.986 | 1.000 | 0.946 |
| hybrid + rerank | 0.957 | 0.986 | 0.986 | 0.969 |

| Generation (hybrid + rerank) | Score |
|---|---|
| Faithfulness (LLM judge, supported claims / claims) | 0.967 |
| Answered (not "I don't know") | 0.986 |

Recall@k: share of questions whose evidence sentence is in a top-k chunk. MRR: mean of 1/rank of the first such chunk.
