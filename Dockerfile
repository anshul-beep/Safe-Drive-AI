# Use a Windows Server image
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Install Python
RUN powershell.exe -Command \
    wget https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe -OutFile python-3.12.0-amd64.exe; \
    Start-Process python-3.12.0-amd64.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait; \
    Remove-Item -Force python-3.12.0-amd64.exe

# Upgrade pip
RUN python -m pip install --upgrade pip

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/Scripts:${PATH}"

# Copy the dlib .whl file
COPY ./dlib-19.24.99-cp312-cp312-win_amd64.whl /tmp/

# Install the dlib package
RUN pip install /tmp/dlib-19.24.99-cp312-cp312-win_amd64.whl

# Copy other necessary files, like requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install the remaining Python dependencies
RUN pip install -r /tmp/requirements.txt

# Copy your source code
COPY ./src /code
WORKDIR /code

# Set environment variables for Django
ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

ARG DJANGO_DEBUG=0
ENV DJANGO_DEBUG=${DJANGO_DEBUG}

# Run commands that do not require the database
RUN python manage.py collectstatic --noinput

# Set the Django default project name
ARG PROJ_NAME="cfehome"

# Create a bash script to run the Django project
RUN printf "#!/bin/bash\n" > ./paracord_runner.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./paracord_runner.sh && \
    printf "python manage.py migrate --no-input\n" >> ./paracord_runner.sh && \
    printf "gunicorn ${PROJ_NAME}.wsgi:application --bind \"0.0.0.0:\$RUN_PORT\"\n" >> ./paracord_runner.sh

# Make the bash script executable
RUN chmod +x paracord_runner.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run the Django project via the runtime script when the container starts
CMD ./paracord_runner.sh
