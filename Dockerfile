# Build arguments for CPU-only or GPU variant
# Set to 'gpu' for production builds that support both GPU and CPU
ARG BUILD_VARIANT=gpu
ARG CUDA_VERSION=12.2.2
ARG CUDNN_VERSION=8

# Base image - use NVIDIA CUDA runtime for GPU variant, or python:3.9-slim for CPU
FROM nvidia/cuda:${CUDA_VERSION}-cudnn${CUDNN_VERSION}-runtime-ubuntu22.04 AS base-gpu
FROM python:3.9-slim AS base-cpu

# Select the appropriate base image based on BUILD_VARIANT
FROM base-${BUILD_VARIANT} AS final

# Re-declare BUILD_VARIANT to make it available in this stage
ARG BUILD_VARIANT
ARG SKIP_MODEL_WARMUP

# Install Python for GPU variant (CUDA image doesn't include it)
RUN if [ "${BUILD_VARIANT}" = "gpu" ]; then \
        apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-dev \
        python3-pip && \
        update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
        python3 -m pip install --upgrade pip; \
    fi

# Install system dependencies, build tools, and libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    tar \
    xz-utils \
    fonts-liberation \
    fontconfig \
    build-essential \
    yasm \
    cmake \
    meson \
    ninja-build \
    nasm \
    libssl-dev \
    libvpx-dev \
    libx264-dev \
    libx265-dev \
    libnuma-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    libspeex-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libgnutls28-dev \
    libaom-dev \
    libdav1d-dev \
    libzimg-dev \
    libwebp-dev \
    git \
    pkg-config \
    autoconf \
    automake \
    libtool \
    libfribidi-dev \
    libharfbuzz-dev \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install SRT from source (latest version using cmake)
RUN git clone https://github.com/Haivision/srt.git && \
    cd srt && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf srt

# Install SVT-AV1 from source
RUN git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
    cd SVT-AV1 && \
    git checkout v0.9.0 && \
    cd Build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf SVT-AV1

# Install libvmaf from source
RUN git clone https://github.com/Netflix/vmaf.git && \
    cd vmaf/libvmaf && \
    meson build --buildtype release && \
    ninja -C build && \
    ninja -C build install && \
    cd ../.. && rm -rf vmaf && \
    ldconfig  # Update the dynamic linker cache

# Manually build and install fdk-aac (since it is not available via apt-get)
RUN git clone https://github.com/mstorsjo/fdk-aac && \
    cd fdk-aac && \
    autoreconf -fiv && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf fdk-aac

# Install libunibreak (required for ASS_FEATURE_WRAP_UNICODE)
RUN git clone https://github.com/adah1972/libunibreak.git && \
    cd libunibreak && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libunibreak

# Build and install libass with libunibreak support and ASS_FEATURE_WRAP_UNICODE enabled
RUN git clone https://github.com/libass/libass.git && \
    cd libass && \
    autoreconf -i && \
    ./configure --enable-libunibreak || { cat config.log; exit 1; } && \
    mkdir -p /app && echo "Config log located at: /app/config.log" && cp config.log /app/config.log && \
    make -j$(nproc) || { echo "Libass build failed"; exit 1; } && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libass

# Build and install FFmpeg with all required features
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg && \
    cd ffmpeg && \
    git checkout n7.0.2 && \
    PKG_CONFIG_PATH="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig" \
    CFLAGS="-I/usr/include/freetype2" \
    LDFLAGS="-L/usr/lib/x86_64-linux-gnu" \
    ./configure --prefix=/usr/local \
        --enable-gpl \
        --enable-pthreads \
        --enable-neon \
        --enable-libaom \
        --enable-libdav1d \
        --enable-libsvtav1 \
        --enable-libvmaf \
        --enable-libzimg \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-libwebp \
        --enable-libmp3lame \
        --enable-libopus \
        --enable-libvorbis \
        --enable-libtheora \
        --enable-libspeex \
        --enable-libass \
        --enable-libfreetype \
        --enable-libharfbuzz \
        --enable-fontconfig \
        --enable-libsrt \
        --enable-filter=drawtext \
        --extra-cflags="-I/usr/include/freetype2 -I/usr/include/libpng16 -I/usr/include" \
        --extra-ldflags="-L/usr/lib/x86_64-linux-gnu -lfreetype -lfontconfig" \
        --enable-gnutls \
    && make -j$(nproc) && \
    make install && \
    cd .. && rm -rf ffmpeg

# Add /usr/local/bin to PATH (if not already included)
ENV PATH="/usr/local/bin:${PATH}"

# Copy fonts into the custom fonts directory
COPY ./fonts /usr/share/fonts/custom

# Rebuild the font cache so that fontconfig can see the custom fonts
RUN fc-cache -f -v

# Set work directory
WORKDIR /app

# Set environment variables for model caching
ENV WHISPER_CACHE_DIR="/app/whisper_cache"
ENV ASR_CACHE_DIR="/app/asr_cache"
ENV HF_HOME="/app/huggingface_cache"

# Create cache directories
RUN mkdir -p ${WHISPER_CACHE_DIR} ${ASR_CACHE_DIR} ${HF_HOME}

# Copy the requirements file first to optimize caching
COPY requirements.txt .

# Install Python dependencies, upgrade pip
# For GPU variant, use python3 -m pip since pip may not be in PATH yet
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt && \
    python3 -m pip install playwright && \
    python3 -m pip install jsonschema

# Install OpenMP library (required for ctranslate2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install CTranslate2 with appropriate CUDA support for GPU variant
# For CPU variant, standard ctranslate2 is already in requirements.txt
RUN if [ "${BUILD_VARIANT}" = "gpu" ]; then \
        # Install CUDA 12.2+ compatible CT2 (version 4.6.0 supports CUDA 12+)
        python3 -m pip install --no-cache-dir ctranslate2==4.6.0; \
    fi

# Create the appuser 
RUN useradd -m appuser 

# Give appuser ownership of the /app directory (including all cache directories)
RUN chown -R appuser:appuser /app

# Important: Switch to the appuser
USER appuser

# Install Playwright Chromium browser as appuser
RUN playwright install chromium

# Copy the rest of the application code (as root to ensure proper ownership)
USER root
COPY --chown=appuser:appuser . .

# Make warm-up script executable
RUN chmod +x /app/scripts/warm_up_model.py || true

# Switch back to appuser
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set BUILD_VARIANT as environment variable for runtime detection
ENV BUILD_VARIANT=${BUILD_VARIANT}

# For CPU-only builds (CI), skip model warmup by default
ENV SKIP_MODEL_WARMUP=${SKIP_MODEL_WARMUP:-false}

RUN echo '#!/bin/bash\n\
# Check if faster-whisper can be imported, fallback to OpenAI Whisper if needed\n\
python /app/init_faster_whisper.py\n\
# Run model warm-up if enabled\n\
if [ "${ENABLE_OPENAI_WHISPER}" != "true" ] && [ "${SKIP_MODEL_WARMUP}" != "true" ]; then\n\
    echo "Running model warm-up..."\n\
    python /app/scripts/warm_up_model.py || echo "Model warm-up failed (non-critical)"\n\
fi\n\
# Start Gunicorn\n\
gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --keep-alive 80 \
    app:app' > /app/run_gunicorn.sh && \
    chmod +x /app/run_gunicorn.sh

# Run the shell script
CMD ["/app/run_gunicorn.sh"]
