# Use Ubuntu as base image
FROM ubuntu:22.04 as base

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python packages in a single layer
RUN apt-get update && apt-get install -y \
    git \
    intltool \
    closure-compiler \
    python3-pip \
    python3-libtorrent \
    python3-geoip \
    python3-dbus \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-ayatanaappindicator3-0.1 \
    python3-pygame \
    libnotify4 \
    librsvg2-common \
    xdg-utils \
    enchant-2 \
    libenchant-2-2 \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install tox

# Create and set working directory
WORKDIR /app

# Create user and set up cache directory
RUN useradd -m deluge \
    && mkdir -p /home/deluge/.cache/pre-commit \
    && chown -R deluge:deluge /home/deluge/.cache

FROM base as runtime

# Switch to deluge user
USER deluge

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/home/deluge/.local/bin:${PATH}"

CMD ["bash"]
