from indexer import vector_store


def retrieve(question, top_k=6):
    # langchain similarity search with scores
    results = vector_store.similarity_search_with_score(question, k=top_k)

    chunks = []
    for doc, score in results:
        m = doc.metadata
        file = m.get("file", "unknown")
        start = m.get("start_line", 0)
        end = m.get("end_line", 0)
        name = m.get("name", "")

        ref = f"{file}:{start}-{end}"
        if name:
            ref += f" ({name})"

        chunks.append({
            "code": doc.page_content,
            "file": file,
            "start_line": start,
            "end_line": end,
            "name": name,
            "language": m.get("language", ""),
            "similarity": round(float(score), 4),
            "reference": ref
        })

    return chunks


def build_context(chunks):
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] {chunk['reference']}\n```{chunk['language']}\n{chunk['code']}\n```")
    return "\n\n".join(parts)
