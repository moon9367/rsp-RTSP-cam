#!/bin/bash

# 라즈베리파이 RTSP 웹캠 시스템 상태 확인 스크립트

echo "🔴 RTSP 웹캠 시스템 상태"
echo "=========================="

echo ""
echo "📊 서비스 상태:"
sudo systemctl status rtsp-cameras.service --no-pager -l

echo ""
echo "📹 연결된 웹캠:"
v4l2-ctl --list-devices

echo ""
echo "🌐 활성 포트:"
sudo netstat -tlnp | grep -E ':(8080|8554|8555|8556|8557)' || echo "활성 포트가 없습니다."

echo ""
echo "💾 메모리 사용량:"
free -h

echo ""
echo "🔥 CPU 사용량:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | awk '{print "CPU 사용률: " $1 "%"}'

echo ""
echo "📁 프로젝트 디렉토리:"
ls -la /home/tspol/rsp-RTSP-cam/
