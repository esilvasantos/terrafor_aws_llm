FROM postgres:16.1

ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary dependencies
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y ca-certificates gnupg && \
    apt-get install -y --no-install-recommends \
    curl \
    unzip \
    wget \
    python3 \
    python3-pip \
    python3-venv \
    sudo \
    lsb-release \
    software-properties-common \
    awscli \
    libpq-dev \
    python3-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Python environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONOPTIMIZE=2   

# Install Terraform
ENV TERRAFORM_VERSION=1.9.8
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | bash

# Create directory for the application (to avoid overwriting the volume)
WORKDIR /app

# Create directory for the virtual environment outside the volume
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy application files before mounting the volume
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Copy initialization script
COPY init.sh /init.sh
RUN chmod +x /init.sh

# System adjustments
RUN echo 'vm.swappiness=10' >> /etc/sysctl.conf && \
    echo 'vm.dirty_ratio=60' >> /etc/sysctl.conf && \
    echo 'vm.dirty_background_ratio=2' >> /etc/sysctl.conf && \
    echo '*       soft    nofile      65535' >> /etc/security/limits.conf && \
    echo '*       hard    nofile      65535' >> /etc/security/limits.conf

# Expose necessary ports
EXPOSE 11434 5001 5432

# Initialization command
CMD ["/init.sh"]

