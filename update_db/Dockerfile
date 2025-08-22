# Use the official AWS Lambda Python image
FROM public.ecr.aws/lambda/python:3.13

# Set working directory
WORKDIR /var/task

# Copy the requirements file from the parent directory and install dependencies.
COPY update_db/requirements.txt .
RUN pip install -r requirements.txt

# Copy all your application files from the current folder into the container.
COPY . .

# Set the CMD to handler.
CMD ["rental_listings_updater.lambda_handler"]