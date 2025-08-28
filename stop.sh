#!/bin/bash

# 라즈베리파이 RTSP 웹캠 시스템 중지 스크립트

echo "🔴 RTSP 웹캠 시스템 중지 중..."

# 시스템 서비스 중지
sudo systemctl stop rtsp-cameras.service

# 실행 중인 Python 프로세스 종료
pkill -f "python3 main.py"

echo "✅ RTSP 웹캠 시스템이 중지되었습니다."
