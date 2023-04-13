FROM python:3.11

WORKDIR /code

# Install dependencies (including dependency for cv2)
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Copy requirements and application code
COPY ./requirements.txt /code/requirements.txt
COPY . /code/app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Start the application
CMD ["python3", "/code/app/main.py"]
