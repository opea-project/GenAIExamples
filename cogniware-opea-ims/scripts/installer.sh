#!/bin/bash

# Exit on error
set -e

# Update system
sudo apt update && sudo apt upgrade -y

# Installation Instructions for CUDA 12.9
echo "Installing CUDA 12.9..."
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget "https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda-repo-ubuntu2204-12-9-local_12.9.0-575.51.03-1_amd64.deb"
sudo dpkg -i "cuda-repo-ubuntu2204-12-9-local_12.9.0-575.51.03-1_amd64.deb"
sudo cp /var/cuda-repo-ubuntu2204-12-9-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-9

# Install system dependencies
sudo apt install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    unzip \
    pkg-config \
    libssl-dev \
    libcurl4-openssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-serial-dev \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    libboost-all-dev \
    ninja-build \
    clang \
    clang-format \
    clang-tidy \
    cppcheck \
    valgrind \
    gdb \
    lldb

# Create and activate virtual environment
python3 -m venv ~/msmartcompute_env
source ~/msmartcompute_env/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    torch \
    torchvision \
    torchaudio \
    transformers \
    accelerate \
    bitsandbytes \
    sentencepiece \
    protobuf \
    safetensors \
    huggingface_hub \
    flash-attn \
    torch-pruning \
    torch-tb-profiler \
    memory_profiler \
    onnx \
    onnxruntime \
    tensorboard \
    prometheus-client \
    grpcio \
    grpcio-tools \
    fastapi \
    uvicorn \
    python-multipart \
    python-jose[cryptography] \
    passlib[bcrypt] \
    python-dotenv \
    pytest \
    pytest-cov \
    black \
    isort \
    mypy \
    pylint \
    bandit \
    safety

# Install CUDA if NVIDIA GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing CUDA..."
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
    sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
    wget https://developer.download.nvidia.com/compute/cuda/12.3.1/local_installers/cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
    sudo dpkg -i cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
    sudo cp /var/cuda-repo-ubuntu2204-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
    sudo apt update
    sudo apt install -y cuda
fi

# Create necessary directories
mkdir -p ~/.msmartcompute/models
mkdir -p ~/.msmartcompute/logs
mkdir -p ~/.msmartcompute/config
mkdir -p ~/.msmartcompute/cache
mkdir -p ~/.msmartcompute/temp

# Create default configuration
cat > ~/.msmartcompute/config/config.yaml << EOL
coordinator:
  address: "localhost:50051"
  max_workers: 4
  worker_timeout: 300
  heartbeat_interval: 30

security:
  secret_key: "your-secret-key-here"
  token_expiry: 3600
  ssl_enabled: false
  ssl_cert: ""
  ssl_key: ""

monitoring:
  prometheus_port: 9090
  metrics_interval: 5
  log_level: "info"
  enable_tracing: true
  tracing_endpoint: "localhost:4317"

resources:
  memory_threshold: 0.8
  gpu_threshold: 0.9
  cpu_threads: 4
  max_batch_size: 32
  max_sequence_length: 4096

models:
  - name: "gemma-2b-it"
    type: "gemma"
    path: "~/.msmartcompute/models/gemma"
    gpu_memory: 4096
    batch_size: 1
    quantization: "4bit"
    precision: "float16"
    max_length: 2048
    temperature: 0.7
    top_p: 0.95
    
  - name: "mistral-7b"
    type: "mistral"
    path: "~/.msmartcompute/models/mistral"
    gpu_memory: 8192
    batch_size: 1
    quantization: "4bit"
    precision: "float16"
    max_length: 4096
    temperature: 0.7
    top_p: 0.95
    
  - name: "llama2-7b-chat"
    type: "llama2"
    path: "~/.msmartcompute/models/llama2"
    gpu_memory: 8192
    batch_size: 1
    quantization: "4bit"
    precision: "float16"
    max_length: 4096
    temperature: 0.7
    top_p: 0.95

optimization:
  use_flash_attention: true
  use_tensor_parallelism: true
  tensor_parallel_size: 2
  use_gradient_checkpointing: true
  use_cpu_offloading: true
  max_memory:
    gpu: "4GiB"
    cpu: "8GiB"
  batch_processing:
    max_batch_size: 8
    strategy: "dynamic"
  kv_cache:
    enabled: true
    max_size: 1024
    type: "flash"
  quantization:
    enabled: true
    type: "4bit"
    compute_dtype: "float16"
    use_double_quant: true
    quant_type: "nf4"
  pruning:
    enabled: false
    type: "structured"
    target_sparsity: 0.3
  distillation:
    enabled: false
    teacher_model: ""
    temperature: 2.0
    alpha: 0.5

logging:
  level: "info"
  format: "json"
  output: "file"
  file: "~/.msmartcompute/logs/msmartcompute.log"
  max_size: 100
  max_files: 5
  include_timestamp: true
  include_thread_id: true
  include_process_id: true

profiling:
  enabled: true
  sampling_rate: 0.1
  output_dir: "~/.msmartcompute/profiling"
  metrics:
    - "inference_time"
    - "memory_usage"
    - "gpu_utilization"
    - "throughput"
    - "latency"
EOL

# Build MSmartCompute
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ ..
cmake --build . --config Release -j$(nproc)

# Install MSmartCompute
sudo cmake --install .

# Create systemd service file
sudo tee /etc/systemd/system/msmartcompute.service << EOL
[Unit]
Description=MSmartCompute Engine Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/.msmartcompute
ExecStart=/usr/local/bin/msmartcompute_engine
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/$USER/msmartcompute_env/lib/python3.8/site-packages

[Install]
WantedBy=multi-user.target
EOL

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable msmartcompute
sudo systemctl start msmartcompute

echo "MSmartCompute installation completed successfully!"
echo "Please check the logs at ~/.msmartcompute/logs/msmartcompute.log" 