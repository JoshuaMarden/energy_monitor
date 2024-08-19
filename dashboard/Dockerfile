FROM python:latest



# Copy the current directory contents into the container at /app
COPY dashboard_script.py .
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip3 install  -r requirements.txt


EXPOSE 8501

EXPOSE 5432

# Run the application --platform "linux/amd64"
CMD ["streamlit", "run", "dashboard_script.py", "--server.port=8501"]