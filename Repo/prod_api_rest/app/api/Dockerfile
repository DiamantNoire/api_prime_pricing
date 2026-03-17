FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /opt/app

COPY prod_api_rest/app/api/requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

COPY dev_build_models /opt/app/dev_build_models
COPY prod_api_rest/app/api /opt/app/api

ENV PYTHONPATH=/opt/app/api:/opt/app/dev_build_models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
