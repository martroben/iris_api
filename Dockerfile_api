# build stage
FROM python:3.10-slim-bullseye AS builder
LABEL stage=iris_api_builder
WORKDIR /api
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# work stage
FROM python:3.10-slim-bullseye
ENV PYTHONUNBUFFERED 1
WORKDIR /api
COPY --from=builder /wheels /wheels
COPY install_packages.sh .
RUN chmod +x ./install_packages.sh && ./install_packages.sh && pip install --no-cache /wheels/* && rm -Rfv /wheels
RUN addgroup --system api_user && adduser --system --group api_user
COPY app.py general.py iris.py sql_operations.py entrypoint.sh ./
# Change /iris_data if mount directory changes
RUN chmod +x ./entrypoint.sh && mkdir -p /iris_data && chown api_user /iris_data
USER api_user
ENTRYPOINT ["./entrypoint.sh"]
