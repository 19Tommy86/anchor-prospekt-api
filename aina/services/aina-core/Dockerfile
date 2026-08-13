FROM python:3.12-slim AS bygg

WORKDIR /app
COPY pyproject.toml README.md ./
COPY aina ./aina
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

# Kjør som ikke-privilegert bruker. Noden står i et hjem, ikke i et datasenter.
RUN useradd --create-home --uid 10001 aina

WORKDIR /app
COPY --from=bygg /install /usr/local
COPY aina ./aina

RUN mkdir -p /app/data && chown -R aina:aina /app
USER aina

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/status')"

CMD ["uvicorn", "aina.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
