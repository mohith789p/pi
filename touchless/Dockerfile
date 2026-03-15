# ===========================
# Dockerfile for Jetson Nano
# Supports Development & Production Modes
# ===========================

# Use official Jetson Nano L4T base image
FROM nvcr.io/nvidia/l4t-base:r35.2.1

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip python3-opencv git curl && \
    rm -rf /var/lib/apt/lists/*

# Using requirements.txt for version control and reproducibility
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy your project code
COPY . /workspace

# Default command for container

# Development mode: opens bash for interactive debugging
CMD ["bash"]

# Production / Deployment mode: automatically runs your app
# CMD ["python3", "main.py"]
