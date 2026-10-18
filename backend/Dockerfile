FROM python:3.13.15-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
ENV HF_HOME=/app/huggingface
RUN python -c "\
from langchain_huggingface import HuggingFaceEmbeddings; \
HuggingFaceEmbeddings( \
    model_name='BAAI/bge-base-en-v1.5', \
    model_kwargs={'device': 'cpu'}, \
    encode_kwargs={'normalize_embeddings': True} \
)"
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# Configure the default endpoint; provide OPENAI_API_KEY at runtime.
ENV OPENAI_API_BASE="https://api.openai.com/v1"
ENV OPENAI_BASE_URL="https://api.openai.com/v1"

CMD ["gunicorn", "-w", "1", "--timeout", "120", "-b", "0.0.0.0:7860", "app:rag_api"]
