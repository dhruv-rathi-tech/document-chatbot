from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from config.config import *

PROMPT_TEMPLATE = ChatPromptTemplate.from_template("""
You are an expert Retrieval-Augmented Generation (RAG) assistant.

Your task is to answer the user's question using ONLY the retrieved context.

Rules:
1. Use only the provided context.
2. Do not fabricate or infer information that is not explicitly present.
3. If the answer cannot be determined from the context, reply exactly:
   "I don't have enough information in the provided documents to answer this question."
4. Combine information from multiple retrieved chunks into one coherent answer when appropriate.
5. Ignore retrieved chunks that are unrelated to the user's question.
6. If the retrieved documents contain conflicting information, clearly mention the conflict.
7. Do NOT include a "Sources" section yourself - it will be added separately.
8. Answer in plain prose only, with no source list, footer, or citations.


############################
Retrieved Context
############################
{context}

############################
Question
############################
{query}

Answer
""")


llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=TEMPERATURE,
)

def generate(query, reranked_results):
    context = "\n\n".join(
        f"[Source: {res['document'].metadata.get('source', 'unknown')}]\n"
        f"{res['document'].page_content}"
        for res in reranked_results
    )

    prompt = PROMPT_TEMPLATE.format_messages(context=context, query=query)
    response = llm.invoke(prompt)
    answer = response.content.strip()

    seen = []
    for res in reranked_results:
        source = res["document"].metadata.get("source", "unknown")
        if source not in seen:
            seen.append(source)
 
    if seen:
        answer += "\n\nSources: " + ", ".join(seen)
 
    return answer
