FROM public.ecr.aws/lambda/python:3.13

# Set working directory
WORKDIR /var/task

# Copy the requirements file
COPY update_db/requirements.txt .
RUN pip install -r requirements.txt

# Copy the Lambda source code
COPY update_db/ .

# Set the CMD to handler.
CMD ["rental_listings_updater.lambda_handler"]
