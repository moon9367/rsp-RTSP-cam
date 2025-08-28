#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import signal
import logging
import threading
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from camera_manager import camera_manager
from rtsp_server import rtsp_server
from web_interface import app

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rtsp_cameras.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class RTSPCameraSystem:
    """RTSP 카메라 시스템 메인 클래스"""
    
    def __init__(self):
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger.info(f"시그널 {signum} 수신됨. 시스템 종료 중...")
        self.shutdown()
    
    def start(self):
        """시스템 시작"""
        try:
            logger.info("라즈베리파이 RTSP 웹캠 시스템 시작 중...")
            
            # 설정 로드
            config.load_config()
            logger.info("설정 로드 완료")
            
            # 카메라 매니저 시작
            logger.info("카메라 매니저 초기화 중...")
            if not camera_manager.start_all():
                logger.warning("일부 카메라 시작 실패")
            
            # RTSP 서버 시작
            logger.info("RTSP 서버 시작 중...")
            if not rtsp_server.start():
                logger.error("RTSP 서버 시작 실패")
                return False
            
            # 웹 인터페이스 시작 (별도 스레드에서)
            logger.info("웹 인터페이스 시작 중...")
            web_thread = threading.Thread(target=self._start_web_interface, daemon=True)
            web_thread.start()
            
            self.is_running = True
            logger.info("시스템 시작 완료!")
            
            # 메인 루프
            self._main_loop()
            
        except Exception as e:
            logger.error(f"시스템 시작 실패: {e}")
            return False
        
        return True
    
    def _start_web_interface(self):
        """웹 인터페이스 시작"""
        try:
            host = config.web_interface['host']
            port = config.web_interface['port']
            debug = config.web_interface['debug']
            
            logger.info(f"웹 인터페이스 시작: http://{host}:{port}")
            app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
            
        except Exception as e:
            logger.error(f"웹 인터페이스 시작 실패: {e}")
    
    def _main_loop(self):
        """메인 루프"""
        logger.info("메인 루프 시작됨. Ctrl+C로 종료할 수 있습니다.")
        
        try:
            while self.is_running and not self.shutdown_event.is_set():
                # 시스템 상태 점검
                self._health_check()
                
                # 30초마다 상태 점검
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("키보드 인터럽트 수신됨")
        except Exception as e:
            logger.error(f"메인 루프 오류: {e}")
        finally:
            self.shutdown()
    
    def _health_check(self):
        """시스템 상태 점검"""
        try:
            # 카메라 상태 점검
            camera_status = camera_manager.get_all_status()
            active_cameras = sum(1 for cam in camera_status.values() if cam['is_running'])
            
            # RTSP 스트림 상태 점검
            rtsp_status = rtsp_server.get_all_status()
            active_streams = sum(1 for stream in rtsp_status.values() if stream['is_streaming'])
            
            logger.info(f"상태 점검 - 카메라: {active_cameras}/{len(camera_status)}, RTSP: {active_streams}/{len(rtsp_status)}")
            
            # 문제가 있는 카메라 재시작 시도
            for camera_id, camera in camera_status.items():
                if not camera['is_running'] and camera['is_connected']:
                    logger.info(f"중지된 카메라 {camera_id} 재시작 시도")
                    camera_manager.start_camera(camera_id)
            
        except Exception as e:
            logger.error(f"상태 점검 오류: {e}")
    
    def shutdown(self):
        """시스템 종료"""
        if not self.is_running:
            return
        
        logger.info("시스템 종료 중...")
        self.is_running = False
        self.shutdown_event.set()
        
        try:
            # RTSP 서버 중지
            logger.info("RTSP 서버 중지 중...")
            rtsp_server.stop()
            
            # 카메라 매니저 중지
            logger.info("카메라 매니저 중지 중...")
            camera_manager.stop_all()
            
            # 설정 저장
            logger.info("설정 저장 중...")
            config.save_config()
            
            logger.info("시스템 종료 완료")
            
        except Exception as e:
            logger.error(f"시스템 종료 오류: {e}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("🔴 라즈베리파이 RTSP 웹캠 시스템")
    print("=" * 60)
    print("4대의 웹캠을 RTSP 스트림으로 변환하여 관리합니다")
    print("웹 인터페이스: http://localhost:8080")
    print("=" * 60)
    
    # 시스템 시작
    system = RTSPCameraSystem()
    
    try:
        if system.start():
            logger.info("시스템이 정상적으로 시작되었습니다.")
        else:
            logger.error("시스템 시작에 실패했습니다.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
