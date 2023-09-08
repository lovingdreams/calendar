# Use an official Python runtime as the base image
FROM python:alpine3.18

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CONFIG_PATH common/configs/dev.cfg

# Set the working directory in the container
RUN rm -rf code
WORKDIR /code

RUN apk update && apk add build-base git

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://workemasteradmin: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@github.com/worketeam/BaseWorke
# Copy the project code into the container
COPY . .
#COPY scripts.sh /code/scripts.sh

RUN python manage.py makemigrations
RUN python manage.py migrate

# Collect static files
RUN rm -rf src/static
RUN python manage.py collectstatic --noinput

EXPOSE 8001

#RUN chmod +x /code/scripts.sh

CMD ["python3","workingHour_consumer.py", "&"]
#CMD ["python","user_grpc_server.py", "&"]
CMD ["python3","manage.py","runserver","0.0.0.0:8001"]
#CMD ["sh","./script.sh"]