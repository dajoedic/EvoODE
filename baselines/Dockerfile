FROM python:3.9-slim

WORKDIR /workspace/EvoODE

RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY baselines/requirements.txt /tmp/baseline-requirements.txt
RUN pip install --no-cache-dir -r /tmp/baseline-requirements.txt

COPY . /workspace/EvoODE

ENV PYTHONPATH=/workspace/EvoODE
ENTRYPOINT ["python", "-m", "baselines.harness"]

