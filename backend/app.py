from flask import Flask, request, jsonify
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from rag_utils import retrieve, rag
import os

EMBED_MODEL = "BAAI/bge-base-en-v1.5"
VECTORSTORE_PATH = "faiss_index"
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "500"))
MAX_K = int(os.getenv("MAX_K", "10"))
MAX_MAX_TOKENS = int(os.getenv("MAX_MAX_TOKENS", "1024"))

rag_api = Flask("NovaCrest API")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

vectorstore = FAISS.load_local(
    VECTORSTORE_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)


def _require_auth():
    expected = os.getenv("API_AUTH_TOKEN")
    if not expected:
        return None

    provided = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "", 1)
    if provided != expected:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@rag_api.before_request
def enforce_api_auth():
    if request.method == "OPTIONS":
        return None
    if request.path in {"/", "/healthz"}:
        return None
    return _require_auth()


@rag_api.get("/")
def home():
    return "Welcome to the NovaCrest AG API!"


@rag_api.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


def _read_json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def _parse_request_query(data):
    query = str(data.get("query", "")).strip()
    if not query:
        return None, jsonify({"error": "Query is required."}), 400
    if len(query) > MAX_QUERY_LENGTH:
        return None, jsonify({"error": f"Query exceeds {MAX_QUERY_LENGTH} characters."}), 400

    try:
        k = int(data.get("k", 2))
    except (TypeError, ValueError):
        return None, jsonify({"error": "k must be an integer."}), 400
    if k < 1 or k > MAX_K:
        return None, jsonify({"error": f"k must be between 1 and {MAX_K}."}), 400

    model_name = str(data.get("model_name", "gpt-4o-mini")).strip() or "gpt-4o-mini"
    try:
        temperature = float(data.get("temperature", 0.0))
        top_p = float(data.get("top_p", 1.0))
        max_tokens = int(data.get("max_tokens", 512))
    except (TypeError, ValueError):
        return None, jsonify({"error": "temperature, top_p, and max_tokens must be numeric."}), 400

    if not 0.0 <= temperature <= 1.0:
        return None, jsonify({"error": "temperature must be between 0.0 and 1.0."}), 400
    if not 0.0 <= top_p <= 1.0:
        return None, jsonify({"error": "top_p must be between 0.0 and 1.0."}), 400
    if max_tokens < 1 or max_tokens > MAX_MAX_TOKENS:
        return None, jsonify({"error": f"max_tokens must be between 1 and {MAX_MAX_TOKENS}."}), 400

    return {
        "query": query,
        "k": k,
        "model_name": model_name,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }, None, None


@rag_api.post("/v1/relevant_chunks")
def relevant_chunks():
    data = _read_json_payload()
    if data is None:
        return jsonify({"error": "Request body must be a JSON object."}), 400

    payload, error_response, status_code = _parse_request_query(data)
    if error_response is not None:
        return error_response, status_code

    chunks = retrieve(query=payload["query"], k=payload["k"], vectorstore=vectorstore)
    return jsonify({"query": payload["query"], "k": payload["k"], "relevant_chunks": chunks})


@rag_api.post("/v1/answer_with_relevant_chunks")
def answer_with_relevant_chunks():
    data = _read_json_payload()
    if data is None:
        return jsonify({"error": "Request body must be a JSON object."}), 400

    payload, error_response, status_code = _parse_request_query(data)
    if error_response is not None:
        return error_response, status_code

    answer, chunks = rag(
        query=payload["query"], k=payload["k"], model_name=payload["model_name"],
        temperature=payload["temperature"], top_p=payload["top_p"], max_tokens=payload["max_tokens"],
        vectorstore=vectorstore
    )
    return jsonify({
        "query": payload["query"], "k": payload["k"], "model_name": payload["model_name"],
        "temperature": payload["temperature"], "top_p": payload["top_p"], "max_tokens": payload["max_tokens"],
        "relevant_chunks": chunks, "answer": answer
    })


@rag_api.post("/v1/answer")
def answer():
    data = _read_json_payload()
    if data is None:
        return jsonify({"error": "Request body must be a JSON object."}), 400

    payload, error_response, status_code = _parse_request_query(data)
    if error_response is not None:
        return error_response, status_code

    generated_answer, _ = rag(
        query=payload["query"], k=payload["k"], model_name=payload["model_name"],
        temperature=payload["temperature"], top_p=payload["top_p"], max_tokens=payload["max_tokens"],
        vectorstore=vectorstore
    )
    return jsonify({"answer": generated_answer})


if __name__ == "__main__":
    rag_api.run(host="0.0.0.0", port=7860, debug=False)
