# ================================
# BUILDER STAGE - Compile FFmpeg & extras
# ================================
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    tar \
    xz-utils \
    cmake \
    meson \
    ninja-build \
    nasm \
    yasm \
    pkg-config \
    autoconf \
    automake \
    libtool \
    # Video codec build dependencies
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
    librav1e-dev \
    libsvtav1-dev \
    libzimg-dev \
    libwebp-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    && rm -rf /var/lib/apt/lists/*

# Build SRT from source
RUN git clone https://github.com/Haivision/srt.git && \
    cd srt && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf srt

# Build SVT-AV1 from source
RUN git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
    cd SVT-AV1 && \
    git checkout v0.9.0 && \
    cd Build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf SVT-AV1

# Build libvmaf from source
RUN git clone https://github.com/Netflix/vmaf.git && \
    cd vmaf/libvmaf && \
    meson build --buildtype release && \
    ninja -C build && \
    ninja -C build install && \
    cd ../.. && rm -rf vmaf && \
    ldconfig

# Build fdk-aac from source
RUN git clone https://github.com/mstorsjo/fdk-aac && \
    cd fdk-aac && \
    autoreconf -fiv && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf fdk-aac

# Build libunibreak
RUN git clone https://github.com/adah1972/libunibreak.git && \
    cd libunibreak && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libunibreak

# Build libass with libunibreak support
RUN git clone https://github.com/libass/libass.git && \
    cd libass && \
    autoreconf -i && \
    ./configure --enable-libunibreak && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libass

# Build FFmpeg with all required features
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
        --enable-librav1e \
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
        --enable-gnutls && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf ffmpeg

# ================================
# FINAL STAGE - Slim runtime image  
# ================================
FROM python:3.9-slim AS final

# Build argument for semantic versioning
ARG BUILD_NUMBER
ENV BUILD_NUMBER=${BUILD_NUMBER}

# Cloud Run port configuration (defaults to 8080)
ENV PORT=8080

# Install only runtime dependencies + curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential runtime libraries
    ca-certificates \
    fonts-liberation \
    fontconfig \
    libssl3 \
    libvpx7 \
    libx264-164 \
    libx265-199 \
    libnuma1 \
    libmp3lame0 \
    libopus0 \
    libvorbis0a \
    libtheora0 \
    libspeex1 \
    libfreetype6 \
    libfontconfig1 \
    libgnutls30 \
    libaom3 \
    libdav1d6 \
    libwebp7 \
    libfribidi0 \
    libharfbuzz0b \
    # Browser dependencies for Playwright
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
    # Health check dependency
    curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy compiled binaries and libraries from builder
COPY --from=builder /usr/local /usr/local

# Update library cache
RUN ldconfig

# Add runtime binaries to PATH
ENV PATH="/usr/local/bin:${PATH}"

# Copy fonts
COPY ./fonts /usr/share/fonts/custom

# Rebuild font cache
RUN fc-cache -f -v

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Set up Whisper cache directory (stateless - tmpfs only)
ENV WHISPER_CACHE_DIR="/tmp/whisper_cache"
RUN mkdir -p ${WHISPER_CACHE_DIR} && chown appuser:appuser ${WHISPER_CACHE_DIR}

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir openai-whisper playwright jsonschema && \
    rm -rf /root/.cache/pip

# Switch to non-root user
USER appuser

# Pre-load Whisper model (will use tmpfs cache at runtime)
RUN python -c "import whisper; whisper.load_model('base')"

# Install Playwright browser
RUN playwright install chromium

# Copy application code
COPY --chown=appuser:appuser . .

# Expose dynamic port for Cloud Run compatibility  
EXPOSE $PORT

# Cloud Run health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy and setup entrypoint script for Cloud Run compatibility
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use ENTRYPOINT to respect Cloud Run's PORT environment variable
ENTRYPOINT ["/app/entrypoint.sh"]
