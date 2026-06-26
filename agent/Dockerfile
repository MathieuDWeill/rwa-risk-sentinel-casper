FROM python:3.11-slim
WORKDIR /app
COPY agent/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/app /app/agent/app
COPY data /app/data
ENV PYTHONPATH=/app
CMD ["python", "-m", "agent.app.main"]
