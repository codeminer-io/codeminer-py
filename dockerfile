# Start from a lightweight base image with a specific Python version
FROM python:3.11-slim

# Install essential packages for builds and supporting tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    libgdbm-dev \
    && rm -rf /var/lib/apt/lists/*

# Set architecture-specific Quarto URL
# This runs at build time to determine the architecture and download the correct Quarto package.
RUN ARCH=$(uname -m) && \
    if [ "$(uname -m)" = "x86_64" ]; then \
    ARCH="amd64"; \
    elif [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then \
    ARCH="arm64"; \
    else \
    echo "Unsupported architecture"; exit 1; \
    fi && \
    curl -fsSL https://github.com/quarto-dev/quarto-cli/releases/download/v1.7.6/quarto-1.7.6-linux-${ARCH}.tar.gz | tar -xz -C /opt \
    && ln -s /opt/quarto-1.7.6/bin/quarto /usr/local/bin/quarto

# Verify Quarto installation
RUN quarto --version

# Install uv for Python and dependency management
ENV UV_INSTALL_DIR="/usr/local/bin"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Configure uv to use in-project virtual environments
ENV UV_PROJECT_ENVIRONMENT=".venv"

# Install ipython and configure default IPython profile
RUN pip install --no-cache-dir ipython && \
    ipython profile create && \
    echo "c.InteractiveShellApp.extensions = ['autoreload']" >> /root/.ipython/profile_default/ipython_config.py && \
    echo "c.InteractiveShellApp.exec_lines = ['%autoreload 2']" >> /root/.ipython/profile_default/ipython_config.py && \
    echo "c.TerminalInteractiveShell.editing_mode = 'vi'" >> /root/.ipython/profile_default/ipython_config.py

# Set work directory (to be replaced in downstream images by project-specific directories)
WORKDIR /app

# Optionally add an entrypoint to make uv commands easier to run in derived images
ENTRYPOINT ["uv"]
