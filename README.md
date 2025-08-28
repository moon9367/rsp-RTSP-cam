# 🔴 라즈베리파이 RTSP 웹캠 시스템

라즈베리파이에서 4대의 웹캠을 동시에 RTSP 스트림으로 변환하여 관리하는 완전한 솔루션입니다.

## ✨ 주요 기능

- **4대 웹캠 동시 지원**: USB 웹캠 4대를 동시에 관리
- **RTSP 스트리밍**: 표준 RTSP 프로토콜로 실시간 스트리밍
- **웹 기반 관리**: 직관적인 웹 인터페이스로 카메라 제어
- **실시간 모니터링**: 각 카메라의 상태와 스트림 품질 모니터링
- **자동 재시작**: 문제 발생 시 자동으로 카메라 재시작
- **시스템 서비스**: 부팅 시 자동 시작 및 백그라운드 실행

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   웹캠 1-4     │    │   카메라 매니저  │    │   RTSP 서버     │
│  (USB 장치)     │───▶│  (OpenCV 기반)   │───▶│  (포트 8554-7)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   웹 인터페이스  │    │   RTSP 클라이언트 │
                       │   (포트 8080)    │    │  (VLC, FFmpeg 등)│
                       └─────────────────┘    └─────────────────┘
```

## 📋 요구사항

### 하드웨어
- 라즈베리파이 4 (권장) 또는 라즈베리파이 3B+
- USB 웹캠 4대
- 최소 4GB RAM (8GB 권장)
- 최소 16GB SD 카드

### 소프트웨어
- Raspberry Pi OS (Bullseye 이상)
- Python 3.8+
- OpenCV 4.x
- Flask 웹 프레임워크

## 🚀 빠른 시작

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd rsp-rtsp-cam
```

### 2. 설치 스크립트 실행
```bash
chmod +x install.sh
./install.sh
```

### 3. 시스템 시작
```bash
sudo systemctl start rtsp-cameras.service
```

### 4. 웹 인터페이스 접속
브라우저에서 `http://라즈베리파이IP:8080` 접속

## 📁 프로젝트 구조

```
rsp-rtsp-cam/
├── main.py                 # 메인 실행 파일
├── config.py              # 설정 관리
├── camera_manager.py      # 카메라 관리
├── rtsp_server.py         # RTSP 서버
├── web_interface.py       # 웹 인터페이스
├── requirements.txt       # Python 의존성
├── install.sh            # 설치 스크립트
├── rtsp-cameras.service  # 시스템 서비스
├── templates/            # 웹 템플릿
│   └── index.html       # 메인 페이지
├── start.sh             # 시작 스크립트
├── stop.sh              # 중지 스크립트
├── status.sh            # 상태 확인 스크립트
└── README.md            # 프로젝트 문서
```

## ⚙️ 설정

### 카메라 설정 (`config.json`)
```json
{
  "cameras": {
    "camera1": {
      "name": "웹캠 1",
      "device": "/dev/video0",
      "resolution": [640, 480],
      "fps": 30,
      "rtsp_port": 8554,
      "enabled": true
    }
  }
}
```

### RTSP 서버 설정
- **포트**: 8554-8557 (카메라별)
- **프로토콜**: RTSP/RTP
- **코덱**: H.264/JPEG
- **최대 클라이언트**: 10명

### 웹 인터페이스 설정
- **포트**: 8080
- **호스트**: 0.0.0.0 (모든 인터페이스)
- **인증**: 없음 (로컬 네트워크용)

## 🔗 RTSP 스트림 URL

각 카메라의 RTSP 스트림에 접근하려면:

```
카메라 1: rtsp://라즈베리파이IP:8554/camera1
카메라 2: rtsp://라즈베리파이IP:8555/camera2
카메라 3: rtsp://라즈베리파이IP:8556/camera3
카메라 4: rtsp://라즈베리파이IP:8557/camera4
```

### 지원하는 RTSP 클라이언트
- **VLC Media Player**
- **FFmpeg**
- **GStreamer**
- **IP Camera Viewer**
- **ONVIF 호환 소프트웨어**

## 🎮 사용법

### 웹 인터페이스
1. **대시보드**: 전체 시스템 상태 및 카메라 현황
2. **카메라 제어**: 개별 카메라 시작/중지/재시작
3. **실시간 스트림**: MJPEG 형식으로 실시간 영상 확인
4. **설정 관리**: 카메라 해상도, FPS 등 설정 변경

### 명령줄 도구
```bash
# 시스템 시작
./start.sh

# 시스템 중지
./stop.sh

# 상태 확인
./status.sh

# 서비스 관리
sudo systemctl start rtsp-cameras.service
sudo systemctl stop rtsp-cameras.service
sudo systemctl status rtsp-cameras.service
```

## 🔧 문제 해결

### 일반적인 문제

#### 1. 웹캠이 인식되지 않음
```bash
# 연결된 비디오 장치 확인
v4l2-ctl --list-devices

# 권한 문제 해결
sudo usermod -a -G video pi
```

#### 2. 포트 충돌
```bash
# 사용 중인 포트 확인
sudo netstat -tlnp | grep :8554

# 방화벽 설정 확인
sudo ufw status
```

#### 3. 성능 문제
- 해상도를 640x480으로 낮춤
- FPS를 15-20으로 조정
- 다른 프로세스 종료

#### 4. 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# 불필요한 서비스 종료
sudo systemctl stop bluetooth
sudo systemctl stop avahi-daemon
```

### 로그 확인
```bash
# 실시간 로그 확인
sudo journalctl -u rtsp-cameras.service -f

# 로그 파일 직접 확인
tail -f /var/log/rtsp_cameras/rtsp_cameras.log
```

## 📊 성능 최적화

### 권장 설정
- **해상도**: 640x480 (기본), 1280x720 (고품질)
- **FPS**: 15-30 (네트워크 상황에 따라)
- **코덱**: H.264 (고품질), JPEG (낮은 지연)
- **버퍼**: 1-2MB (메모리와 지연시간 균형)

### 네트워크 최적화
- 유선 연결 권장 (WiFi보다 안정적)
- QoS 설정으로 RTSP 트래픽 우선순위 지정
- 방화벽에서 필요한 포트만 개방

## 🔒 보안 고려사항

### 현재 상태
- 인증 없음 (로컬 네트워크용)
- 모든 인터페이스에서 접근 가능
- RTSP 스트림 암호화 없음

### 보안 강화 권장사항
```bash
# 방화벽 설정
sudo ufw enable
sudo ufw allow from 192.168.1.0/24 to any port 8080
sudo ufw allow from 192.168.1.0/24 to any port 8554

# 네트워크 격리
# 별도 VLAN 또는 네트워크 세그먼트 사용
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🙏 감사의 말

- OpenCV 커뮤니티
- Flask 개발팀
- Raspberry Pi 재단
- 모든 기여자들

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. **Issues**: GitHub Issues에 문제 보고
2. **Wiki**: 프로젝트 Wiki에서 자세한 문서 확인
3. **Discussions**: GitHub Discussions에서 토론 참여

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**
