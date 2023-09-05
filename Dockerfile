## Use the official Python image as the base image
#FROM python:3.9
#
## Set the working directory to /app
#WORKDIR /app
#
## Copy the requirements.txt file to /app
#COPY requirements.txt /app
#
## Install the dependencies
#RUN pip install -r requirements.txt
#
## Copy the app.py file to /app
#COPY app.py /app
#
## Expose port 5000 for the Flask app
#EXPOSE 5000
#
## Run the app.py file when the container starts
#CMD ["python", "app.py"]
## Install wait-for-it
##RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /wait-for-it.sh
##RUN chmod +x /wait-for-it.sh
##
### Change the CMD to use wait-for-it
##CMD ["/wait-for-it.sh", "db:3306", "--", "python", "app.py"]

# Use the official Python image as the base image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file to /app
COPY requirements.txt /app

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the app.py file to /app
COPY app.py /app

# Install Gunicorn
RUN pip install gunicorn

# Expose port 5000 for the Flask app
EXPOSE 5000

# Run the app.py file with Gunicorn when the container starts
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
