# Start from a lightweight base image with a specific Python version
FROM python:3.11-slim

# Install essential packages for pyenv and Python builds
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

# Install pyenv for Python version management
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
RUN curl https://pyenv.run | bash

# Install pipx and use it to install poetry
ENV PIPX_BIN_DIR="/root/.local/bin"
ENV PATH="$PIPX_BIN_DIR:$PATH"
RUN pip install --no-cache-dir pipx && \
    pipx install poetry

# Install commonly used Python versions with pyenv for flexibility
RUN pyenv install 3.9.13 && pyenv install 3.11.6

# Set a default global Python version (can be overridden by individual projects)
RUN pyenv global 3.11.6

# Configure poetry to create virtual environments within each project directory
RUN poetry config virtualenvs.in-project true

# Install ipython and configure default IPython profile
RUN pip install ipython && \
    ipython profile create && \
    echo "c.InteractiveShellApp.extensions = ['autoreload']" >> /root/.ipython/profile_default/ipython_config.py && \
    echo "c.InteractiveShellApp.exec_lines = ['%autoreload 2']" >> /root/.ipython/profile_default/ipython_config.py && \
    echo "c.TerminalInteractiveShell.editing_mode = 'vi'" >> /root/.ipython/profile_default/ipython_config.py

# Set work directory (to be replaced in downstream images by project-specific directories)
WORKDIR /app

# Expose poetry and pyenv paths for downstream images
ENV PATH="$PYENV_ROOT/shims:$PIPX_BIN_DIR:$PATH"

# Optionally add an entrypoint to make poetry commands easier to run in derived images
ENTRYPOINT ["poetry"]