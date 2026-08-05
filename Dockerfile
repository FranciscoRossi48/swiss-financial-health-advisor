FROM python:3.12-slim

# apply upstream Debian security patches at build time, since the base image tag
# itself is not rebuilt often enough to stay ahead of newly disclosed OS CVEs
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src/ src/
COPY app/ app/
COPY scripts/ scripts/

RUN pip install --no-cache-dir ".[app,api]"

RUN python scripts/build_demo_data.py

EXPOSE 8501

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
