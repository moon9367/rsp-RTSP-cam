#!/bin/bash

# 라즈베리파이 RTSP 웹캠 시스템 설치 스크립트
# 이 스크립트는 라즈베리파이에서 실행되어야 합니다.

set -e

echo "🔴 라즈베리파이 RTSP 웹캠 시스템 설치 시작"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 업데이트
print_status "시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
print_status "필수 패키지 설치 중..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-opencv \
    libopencv-dev \
    python3-dev \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    git \
    curl \
    wget \
    v4l-utils

# USB 웹캠 지원 패키지
print_status "USB 웹캠 지원 패키지 설치 중..."
sudo apt install -y \
    v4l-utils \
    uv4l \
    uv4l-server \
    uv4l-uvc \
    uv4l-xscreen \
    uv4l-mjpegstream \
    uv4l-demos \
    uv4l-tools

# Python 가상환경 생성
print_status "Python 가상환경 생성 중..."
python3 -m venv venv
source venv/bin/activate

# Python 패키지 설치
print_status "Python 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 웹캠 장치 확인
print_status "연결된 웹캠 장치 확인 중..."
echo "사용 가능한 비디오 장치:"
v4l2-ctl --list-devices

# 웹캠 테스트
print_status "웹캠 테스트 중..."
if command -v v4l2-ctl &> /dev/null; then
    for device in /dev/video*; do
        if [ -e "$device" ]; then
            echo "테스트 중: $device"
            v4l2-ctl -d "$device" --list-formats-ext
        fi
    done
fi

# 시스템 서비스 설치
print_status "시스템 서비스 설치 중..."
sudo cp rtsp-cameras.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rtsp-cameras.service

# 권한 설정
print_status "권한 설정 중..."
sudo usermod -a -G video pi
sudo usermod -a -G gpio pi

# 로그 디렉토리 생성
print_status "로그 디렉토리 생성 중..."
sudo mkdir -p /var/log/rtsp_cameras
sudo chown pi:pi /var/log/rtsp_cameras

# 설정 파일 생성
print_status "기본 설정 파일 생성 중..."
if [ ! -f config.json ]; then
    cat > config.json << 'EOF'
{
  "cameras": {
    "camera1": {
      "name": "웹캠 1",
      "device": "/dev/video0",
      "resolution": [640, 480],
      "fps": 30,
      "rtsp_port": 8554,
      "rtsp_path": "/camera1",
      "enabled": true
    },
    "camera2": {
      "name": "웹캠 2",
      "device": "/dev/video1",
      "resolution": [640, 480],
      "fps": 30,
      "rtsp_port": 8555,
      "rtsp_path": "/camera2",
      "enabled": true
    },
    "camera3": {
      "name": "웹캠 3",
      "device": "/dev/video2",
      "resolution": [640, 480],
      "fps": 30,
      "rtsp_port": 8556,
      "rtsp_path": "/camera3",
      "enabled": true
    },
    "camera4": {
      "name": "웹캠 4",
      "device": "/dev/video3",
      "resolution": [640, 480],
      "fps": 30,
      "rtsp_port": 8557,
      "rtsp_path": "/camera4",
      "enabled": true
    }
  },
  "rtsp_server": {
    "host": "0.0.0.0",
    "base_port": 8554,
    "max_clients": 10,
    "buffer_size": 1048576,
    "timeout": 30
  },
  "web_interface": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/rtsp_cameras/rtsp_cameras.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
EOF
    print_success "기본 설정 파일 생성됨"
fi

# 방화벽 설정
print_status "방화벽 설정 중..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8080/tcp  # 웹 인터페이스
    sudo ufw allow 8554/tcp  # RTSP 카메라 1
    sudo ufw allow 8555/tcp  # RTSP 카메라 2
    sudo ufw allow 8556/tcp  # RTSP 카메라 3
    sudo ufw allow 8557/tcp  # RTSP 카메라 4
    print_success "방화벽 규칙 추가됨"
fi

# 시작 스크립트 생성
print_status "시작 스크립트 생성 중..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
EOF

chmod +x start.sh

# 중지 스크립트 생성
print_status "중지 스크립트 생성 중..."
cat > stop.sh << 'EOF'
#!/bin/bash
sudo systemctl stop rtsp-cameras.service
echo "RTSP 카메라 시스템이 중지되었습니다."
EOF

chmod +x stop.sh

# 상태 확인 스크립트 생성
print_status "상태 확인 스크립트 생성 중..."
cat > status.sh << 'EOF'
#!/bin/bash
echo "🔴 RTSP 카메라 시스템 상태"
echo "=========================="
echo "서비스 상태:"
sudo systemctl status rtsp-cameras.service --no-pager -l
echo ""
echo "연결된 웹캠:"
v4l2-ctl --list-devices
echo ""
echo "활성 포트:"
sudo netstat -tlnp | grep -E ':(8080|8554|8555|8556|8557)'
EOF

chmod +x status.sh

# README 파일 생성
print_status "README 파일 생성 중..."
cat > README.md << 'EOF'
# 라즈베리파이 RTSP 웹캠 시스템

4대의 웹캠을 RTSP 스트림으로 변환하여 관리하는 시스템입니다.

## 기능

- 4대 웹캠 동시 지원
- RTSP 스트리밍
- 웹 기반 관리 인터페이스
- 실시간 모니터링
- 자동 재시작 기능

## 사용법

### 시작
```bash
./start.sh
# 또는
sudo systemctl start rtsp-cameras.service
```

### 중지
```bash
./stop.sh
# 또는
sudo systemctl stop rtsp-cameras.service
```

### 상태 확인
```bash
./status.sh
# 또는
sudo systemctl status rtsp-cameras.service
```

### 웹 인터페이스
브라우저에서 `http://라즈베리파이IP:8080` 접속

### RTSP 스트림
- 카메라 1: rtsp://라즈베리파이IP:8554/camera1
- 카메라 2: rtsp://라즈베리파이IP:8555/camera2
- 카메라 3: rtsp://라즈베리파이IP:8556/camera3
- 카메라 4: rtsp://라즈베리파이IP:8557/camera4

## 설정

`config.json` 파일에서 카메라 설정을 수정할 수 있습니다.

## 로그

로그 파일: `/var/log/rtsp_cameras/rtsp_cameras.log`

## 문제 해결

1. 웹캠이 인식되지 않는 경우:
   ```bash
   v4l2-ctl --list-devices
   ```

2. 권한 문제:
   ```bash
   sudo usermod -a -G video pi
   ```

3. 포트 충돌:
   ```bash
   sudo netstat -tlnp | grep :8554
   ```
EOF

print_success "README 파일 생성됨"

# 설치 완료 메시지
echo ""
echo "🎉 설치 완료!"
echo "=============="
echo ""
echo "다음 명령어로 시스템을 시작할 수 있습니다:"
echo "  sudo systemctl start rtsp-cameras.service"
echo ""
echo "웹 인터페이스에 접속하려면:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "RTSP 스트림 URL:"
echo "  카메라 1: rtsp://$(hostname -I | awk '{print $1}'):8554/camera1"
echo "  카메라 2: rtsp://$(hostname -I | awk '{print $1}'):8555/camera2"
echo "  카메라 3: rtsp://$(hostname -I | awk '{print $1}'):8556/camera3"
echo "  카메라 4: rtsp://$(hostname -I | awk '{print $1}'):8557/camera4"
echo ""
echo "시스템 상태 확인:"
echo "  ./status.sh"
echo ""
echo "자동 시작 설정 (부팅 시 자동 시작):"
echo "  sudo systemctl enable rtsp-cameras.service"
echo ""

print_success "라즈베리파이 RTSP 웹캠 시스템 설치가 완료되었습니다!"
