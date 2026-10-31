FROM python:3.12-slim
WORKDIR /app
COPY telemetry_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY telemetry_service ./telemetry_service
EXPOSE 8083
CMD ["uvicorn", "telemetry_service.main:app", "--host", "0.0.0.0", "--port", "8083"]
