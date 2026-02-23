FROM python:3.12-slim

# Create user first
RUN useradd -m appuser
WORKDIR /app
RUN chown appuser:appuser /app

# Switch to user for package installation to ensure home dir and cache belong to appuser
USER appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Build-time dependencies
RUN pip install --no-cache-dir --upgrade --default-timeout=100 torch --index-url https://download.pytorch.org/whl/cpu \
    --trusted-host download.pytorch.org \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --retries 10

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade --default-timeout=100 -r requirements.txt \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --retries 10

COPY --chown=appuser:appuser . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
