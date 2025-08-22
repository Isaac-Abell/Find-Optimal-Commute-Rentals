# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.13

# Install dependencies
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    sqlalchemy \
    psycopg2-binary \
    geopy \
    googlemaps \
    tls_client \
    homeharvest \
    requests \
    pydantic \
    tenacity

# Copy your Lambda function code
COPY rental_listings_updater.py ${LAMBDA_TASK_ROOT}/
COPY config.py ${LAMBDA_TASK_ROOT}/
COPY db.py ${LAMBDA_TASK_ROOT}/
COPY commute.py ${LAMBDA_TASK_ROOT}/

# Lambda entrypoint
CMD ["rental_listings_updater.lambda_handler"]
