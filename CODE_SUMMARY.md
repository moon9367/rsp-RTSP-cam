# rsp-RTSP-cam 코드 요약

USB 카메라 4대를 RTSP 프로토콜로 스트리밍하는 Raspberry Pi 기반 카메라 시스템

## 프로젝트 구조

```
rsp-RTSP-cam/
├── main.py              # 메인 진입점 (시스템 초기화 및 생명주기 관리)
├── config.py            # 설정 관리 (카메라, 서버, 로깅 등)
├── camera_manager.py    # USB 카메라 캡처 및 관리
├── rtsp_server.py       # RTSP/RTP 스트리밍 서버 구현
├── web_interface.py     # Flask 기반 웹 대시보드 + REST API
├── test_cameras.py      # 카메라 하드웨어 테스트 유틸리티
├── templates/index.html # 웹 UI 대시보드
├── requirements.txt     # Python 의존성
├── install.sh / start.sh / stop.sh / status.sh  # 운영 스크립트
└── rtsp-cameras.service # systemd 서비스 파일
```

## 핵심 모듈

| 파일 | 역할 |
|------|------|
| **main.py** | 시스템 오케스트레이터. 설정 로드 → 카메라 매니저 → RTSP 서버 → 웹 인터페이스 순으로 기동. 30초마다 헬스체크, SIGINT/SIGTERM 안전 종료 |
| **config.py** | Arducam 1~4 설정 (`/dev/video1,4,9,12`), 해상도 1280x720@30fps, RTSP 포트 8554~8557, 웹 포트 8080 |
| **camera_manager.py** | OpenCV(V4L2)로 USB 카메라 프레임 캡처. 3회 재시도, FPS 계산, 타임스탬프 오버레이, 5프레임 버퍼. USB 대역폭 보호를 위해 5초 간격 순차 기동 |
| **rtsp_server.py** | 소켓 기반 RTSP 프로토콜 (OPTIONS/DESCRIBE/SETUP/PLAY/TEARDOWN). JPEG → RTP 패킷 전송. 다중 클라이언트 지원 |
| **web_interface.py** | Flask REST API — 카메라 제어, 스냅샷(JPEG), MJPEG 스트리밍, 시스템 상태, 설정 변경 |

## 동작 흐름

```
USB 카메라 → OpenCV 캡처 → 프레임 버퍼
                              ├─→ RTSP/RTP (포트 8554~8557) → VLC, FFmpeg 등
                              ├─→ MJPEG/HTTP (포트 8080)    → 웹 브라우저
                              └─→ JPEG 스냅샷               → REST API
```

1. **시작**: `main.py` 실행 → 설정 로드 → 카메라 순차 시작 → RTSP 서버 바인딩 → 웹 서버 시작
2. **스트리밍**: 각 카메라가 독립 스레드에서 프레임 캡처, RTSP/웹에 동시 제공
3. **모니터링**: 30초 간격 헬스체크로 장애 카메라 자동 재시작
4. **종료**: SIGINT/SIGTERM으로 안전하게 리소스 해제

## 주요 의존성

- **opencv-python** — 카메라 캡처 및 영상 처리
- **numpy** — 수치 연산
- **flask** — 웹 서버 및 REST API

## 설계 특징

- **이중 출력**: RTSP(전문 도구) + MJPEG(웹 브라우저) 동시 지원
- **순차 기동**: USB 버스 과부하 방지 5초 간격
- **자동 복구**: 헬스체크 기반 장애 카메라 자동 재시작
- **systemd 통합**: OS 서비스 등록으로 부팅 시 자동 시작
