FROM public.ecr.aws/lambda/python:3.13

WORKDIR /var/task

# Copy requirements from lambda folder
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy Lambda code
COPY . .

CMD ["listings.lambda_handler"]
