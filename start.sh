#!/bin/bash

# 라즈베리파이 RTSP 웹캠 시스템 시작 스크립트

echo "🔴 RTSP 웹캠 시스템 시작 중..."

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
else
    echo "가상환경을 찾을 수 없습니다. 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    echo "필요한 패키지 설치 중..."
    pip install -r requirements.txt
fi

# 메인 프로그램 실행
echo "메인 프로그램 시작 중..."
python3 main.py
