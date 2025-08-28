#!/bin/bash

# 라즈베리파이 RTSP 웹캠 시스템 권한 설정 스크립트

echo "🔧 권한 설정 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 현재 사용자 확인
CURRENT_USER=$(whoami)
print_status "현재 사용자: $CURRENT_USER"

# 비디오 그룹에 사용자 추가
print_status "비디오 그룹에 사용자 추가 중..."
sudo usermod -a -G video $CURRENT_USER

# GPIO 그룹에 사용자 추가
print_status "GPIO 그룹에 사용자 추가 중..."
sudo usermod -a -G gpio $CURRENT_USER

# 로그 디렉토리 생성 및 권한 설정
print_status "로그 디렉토리 생성 중..."
sudo mkdir -p /var/log/rtsp_cameras
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/rtsp_cameras

# 프로젝트 디렉토리 권한 확인
print_status "프로젝트 디렉토리 권한 확인 중..."
ls -la /home/$CURRENT_USER/rsp-RTSP-cam/

# 방화벽 설정
print_status "방화벽 설정 중..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8080/tcp  # 웹 인터페이스
    sudo ufw allow 8554/tcp  # RTSP 카메라 1
    sudo ufw allow 8555/tcp  # RTSP 카메라 2
    sudo ufw allow 8556/tcp  # RTSP 카메라 3
    sudo ufw allow 8557/tcp  # RTSP 카메라 4
    print_success "방화벽 규칙 추가됨"
else
    print_warning "ufw가 설치되지 않았습니다."
fi

# 스크립트 실행 권한 설정
print_status "스크립트 실행 권한 설정 중..."
chmod +x start.sh
chmod +x stop.sh
chmod +x status.sh
chmod +x setup-permissions.sh

print_success "권한 설정 완료!"
print_warning "새 그룹을 적용하려면 재로그인이 필요할 수 있습니다."
print_status "또는 다음 명령어를 실행하세요: newgrp video"
