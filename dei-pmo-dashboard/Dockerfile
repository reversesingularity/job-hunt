FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py config.py data_access.py generate_mock_data.py ./
COPY views ./views
COPY data/csv ./data/csv
COPY .streamlit ./.streamlit

# DuckDB is gitignored — regenerate seeded mock portfolio at build time
RUN python generate_mock_data.py

ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080

# Railway sets PORT (typically 8080)
CMD streamlit run app.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.headless=true
