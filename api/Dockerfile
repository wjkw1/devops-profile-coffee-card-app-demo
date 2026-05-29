# ── Build stage ──────────────────────────────────────────────────────────────
FROM public.ecr.aws/lambda/python:3.12 AS builder
RUN dnf install -y gcc make
COPY requirements.txt .
RUN pip install --no-cache-dir -t /packages -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM public.ecr.aws/lambda/python:3.12 AS runtime

WORKDIR /var/task

COPY --from=builder /packages /var/packages
COPY handler.py .
COPY app/ app/

ENV PYTHONPATH=/var/packages
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["handler.handler"]
