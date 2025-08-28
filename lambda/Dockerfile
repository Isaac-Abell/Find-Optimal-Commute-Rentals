FROM public.ecr.aws/lambda/python:3.13

WORKDIR /var/task

# Copy requirements file
COPY lambda/requirements.txt .
RUN pip install -r requirements.txt

# Copy Lambda code
COPY lambda/ .
COPY config/ config/

CMD ["lambda_handler.lambda_handler"]