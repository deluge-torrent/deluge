FROM ubuntu:22.04

# Update the package list and install any necessary packages
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    curl \
    git \
    python3 \
    python3-pip \
    pipx \
    && pipx install tox

# Clean up the package list
#rm -rf /var/lib/apt/lists/*

# Set the working directory
#WORKDIR /app

# Copy the current directory contents into the container at /app
#COPY . /app

# Specify the command to run on container start
CMD ["bash"]
