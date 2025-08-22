FROM public.ecr.aws/lambda/python:3.13

WORKDIR /var/task

# Copy requirements from lambda folder
COPY lambda/requirements.txt .
RUN pip install -r requirements.txt

# Copy Lambda code
COPY lambda/ . 

CMD ["listings.lambda_handler"]