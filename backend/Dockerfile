FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-spa libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
# torch/torchvision CPU-only: evita arrastrar ~2GB de librerías CUDA de NVIDIA que no se usan
# (la inferencia OCR corre en CPU dentro del contenedor).
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -e .
COPY folletos_ocr ./folletos_ocr
COPY api ./api
COPY streamlit_app.py ./

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
