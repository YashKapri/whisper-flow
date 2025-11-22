# USE CUDA 11.8 (The Golden Version for faster-whisper 0.10.1)
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install System Dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    libpq-dev \
    gcc \
    git \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Alias
RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Install Python Libraries with Build Fixes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip

# FIX: Install old Cython first to prevent 'av' build error
RUN pip install --no-cache-dir "Cython<3.0" "pyyaml"

# Install main requirements
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY . .