FROM public.ecr.aws/lambda/python:3.13

# Set working directory
WORKDIR /var/task

# Copy the requirements file
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Lambda source code
COPY . .

# Set the CMD to handler.
CMD ["listings.lambda_handler"]
