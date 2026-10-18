from langchain_openai import ChatOpenAI
import os
import sys

def retrieve(query: str, k: int = 2, vectorstore=None) -> list[str]:
    results = vectorstore.similarity_search(query, k=k)
    return [
        f"Content:\n{r.page_content}\n\nMetadata:\n{r.metadata}"
        for r in results
    ]

def generate(query, retrieved_chunks, model) -> str:
    prompt = f"""
    You are an AI assistant answering questions about Salesforce CRM using
    only the information provided in the retrieved Salesforce documentation.

    User Query:
    {query}

    Retrieved Salesforce Documentation:
    {retrieved_chunks}

    Rules:
    1. Answer the question using only information explicitly supported by the
      retrieved documentation.
    2. Do not use outside knowledge, assumptions, or information that is not
      present in the retrieved documentation.
    3. Answer the user\'s specific question directly and completely.
    4. When the documentation provides configuration steps, setup instructions,
      procedures, or troubleshooting steps, present them clearly and in the
      correct order.
    5. Preserve important Salesforce-specific details.
    6. Do not invent Salesforce features.
    7. Include prerequisites or conditions when relevant.
    8. If there is not enough information, respond exactly with:
      "The available documents do not contain enough information to answer this question."
    9. Identify conflicting information clearly.
    10. Do not include unrelated information.
    11. Keep the response concise, clear, and easy to understand.

    Answer:
    """
    return model.invoke(prompt)

def rag(query: str, k: int = 2, model_name: str = "gpt-4o-mini", temperature: float = 0.0, top_p: float = 1.0, max_tokens: int = 512, vectorstore=None):
    # Obtain variables with fallbacks
    api_base = os.getenv('OPENAI_API_BASE') or os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1'
    api_key = os.getenv('OPENAI_API_KEY')

    # Secure Diagnostics
    print("[NovaCrest Diagnostic] Active API Base:", api_base, file=sys.stderr)
    if not api_key:
        print("[NovaCrest Error] OPENAI_API_KEY environment variable is empty or missing inside the container!", file=sys.stderr)
        raise ValueError("OPENAI_API_KEY is missing from the running container environment. Please check your docker run command mapping.")
    else:
        print(f"[NovaCrest Diagnostic] OPENAI_API_KEY detected (Length: {len(api_key)}, Starts with: {api_key[:8]}...)", file=sys.stderr)

    model = ChatOpenAI( 
        model=model_name,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        openai_api_key=api_key,
        openai_api_base=api_base
    )
    retrieved_chunks = retrieve(query=query, k=k, vectorstore=vectorstore)
    answer = generate(query=query, retrieved_chunks=retrieved_chunks, model=model)
    return answer.content, retrieved_chunks
