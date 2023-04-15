FROM python:3.11

WORKDIR /code

# Install dependencies 
RUN apt-get update 

# Copy requirements
COPY ./requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Start the application
CMD ["python3", "/code/AsyncQueue/main.py"]