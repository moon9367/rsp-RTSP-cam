#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import threading
import time
import logging
from typing import Dict, Optional, Tuple
from config import config

class Camera:
    """개별 웹캠을 관리하는 클래스"""
    
    def __init__(self, camera_id: str, camera_config: Dict):
        self.camera_id = camera_id
        self.config = camera_config
        self.cap = None
        self.is_running = False
        self.frame_buffer = None
        self.last_frame_time = 0
        self.frame_count = 0
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # 로깅 설정
        self.logger = logging.getLogger(f"Camera_{camera_id}")
        
    def initialize(self) -> bool:
        """카메라 초기화"""
        try:
            device = self.config['device']
            # V4L2 백엔드 직접 지정
            self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                self.logger.error(f"카메라 {device}를 열 수 없습니다.")
                return False
            
            # 해상도 및 FPS 설정
            width, height = self.config['resolution']
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config['fps'])
            
            # 버퍼 크기 설정 (더 큰 버퍼)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)
            
            # 추가 카메라 설정
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            
            # 카메라 안정화를 위한 대기
            time.sleep(3)  # 1초 → 3초로 증가
            
            # 초기 프레임 읽기 테스트
            ret, test_frame = self.cap.read()
            if not ret:
                self.logger.warning(f"카메라 {self.config['name']} 초기 프레임 읽기 실패")
                # 재시도
                time.sleep(2)
                ret, test_frame = self.cap.read()
                if not ret:
                    self.logger.error(f"카메라 {self.config['name']} 재시도 후에도 프레임 읽기 실패")
                    return False
            
            self.logger.info(f"카메라 {self.config['name']} 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"카메라 초기화 실패: {e}")
            return False
    
    def start(self):
        """카메라 스트리밍 시작"""
        if self.cap is None or not self.cap.isOpened():
            if not self.initialize():
                return False
        
        self.is_running = True
        self.logger.info(f"카메라 {self.config['name']} 스트리밍 시작")
        return True
    
    def stop(self):
        """카메라 스트리밍 중지"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.logger.info(f"카메라 {self.config['name']} 스트리밍 중지")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """현재 프레임 반환 (재시도 로직 포함)"""
        if not self.is_running or self.cap is None:
            return None
        
        try:
            # 최대 3번 재시도
            for attempt in range(3):
                ret, frame = self.cap.read()
                if ret:
                    # FPS 계산
                    current_time = time.time()
                    self.frame_count += 1
                    
                    if current_time - self.fps_start_time >= 1.0:
                        self.fps_counter = self.frame_count
                        self.frame_count = 0
                        self.fps_start_time = current_time
                    
                    # 프레임 정보 오버레이
                    frame_with_info = self.add_frame_info(frame)
                    self.frame_buffer = frame_with_info
                    self.last_frame_time = current_time
                    
                    return frame_with_info
                else:
                    if attempt < 2:  # 마지막 시도가 아니면
                        self.logger.warning(f"카메라 {self.config['name']} 프레임 읽기 실패 (시도 {attempt + 1}/3)")
                        time.sleep(0.1)  # 잠시 대기 후 재시도
                        continue
                    else:
                        self.logger.warning(f"카메라 {self.config['name']}에서 프레임을 읽을 수 없습니다.")
                        return None
                
        except Exception as e:
            self.logger.error(f"프레임 읽기 오류: {e}")
            return None
    
    def add_frame_info(self, frame: np.ndarray) -> np.ndarray:
        """프레임에 정보 오버레이 추가"""
        try:
            # 현재 시간
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # FPS 정보
            fps_text = f"FPS: {self.fps_counter}"
            
            # 카메라 이름
            camera_name = self.config['name']
            
            # 정보를 프레임에 추가
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (0, 255, 0), 2)
            cv2.putText(frame, fps_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (0, 255, 0), 2)
            cv2.putText(frame, camera_name, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, (0, 255, 0), 2)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"프레임 정보 추가 실패: {e}")
            return frame
    
    def get_status(self) -> Dict:
        """카메라 상태 정보 반환"""
        return {
            'id': self.camera_id,
            'name': self.config['name'],
            'is_running': self.is_running,
            'is_connected': self.cap is not None and self.cap.isOpened(),
            'fps': self.fps_counter,
            'resolution': self.config['resolution'],
            'last_frame_time': self.last_frame_time,
            'device': self.config['device']
        }

class CameraManager:
    """여러 카메라를 관리하는 매니저 클래스"""
    
    def __init__(self):
        self.cameras: Dict[str, Camera] = {}
        self.is_running = False
        self.logger = logging.getLogger("CameraManager")
        
        # 활성화된 카메라 초기화
        self._initialize_cameras()
    
    def _initialize_cameras(self):
        """설정에 따라 카메라들 초기화"""
        for camera_id, camera_config in config.cameras.items():
            if camera_config.get('enabled', False):
                camera = Camera(camera_id, camera_config)
                self.cameras[camera_id] = camera
                self.logger.info(f"카메라 {camera_config['name']} 등록됨")
    
    def start_all(self) -> bool:
        """모든 카메라 시작 (순차적으로)"""
        try:
            success_count = 0
            for camera_id, camera in self.cameras.items():
                self.logger.info(f"카메라 {camera_id} 시작 중...")
                if camera.start():
                    success_count += 1
                    self.logger.info(f"카메라 {camera_id} 시작 성공")
                    # 카메라 간 간격을 두어 USB 대역폭 분산
                    time.sleep(5)  # 2초 → 5초로 증가
                else:
                    self.logger.error(f"카메라 {camera_id} 시작 실패")
            
            self.is_running = success_count > 0
            self.logger.info(f"{success_count}/{len(self.cameras)} 카메라 시작됨")
            return self.is_running
            
        except Exception as e:
            self.logger.error(f"카메라 시작 실패: {e}")
            return False
    
    def stop_all(self):
        """모든 카메라 중지"""
        for camera in self.cameras.values():
            camera.stop()
        self.is_running = False
        self.logger.info("모든 카메라 중지됨")
    
    def start_camera(self, camera_id: str) -> bool:
        """특정 카메라 시작"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].start()
        return False
    
    def stop_camera(self, camera_id: str):
        """특정 카메라 중지"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
    
    def get_camera_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """특정 카메라의 프레임 반환"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame()
        return None
    
    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """모든 카메라의 프레임 반환"""
        frames = {}
        for camera_id, camera in self.cameras.items():
            frame = camera.get_frame()
            if frame is not None:
                frames[camera_id] = frame
        return frames
    
    def get_camera_status(self, camera_id: str) -> Optional[Dict]:
        """특정 카메라 상태 반환"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_status()
        return None
    
    def get_all_status(self) -> Dict[str, Dict]:
        """모든 카메라 상태 반환"""
        status = {}
        for camera_id, camera in self.cameras.items():
            status[camera_id] = camera.get_status()
        return status
    
    def add_camera(self, camera_id: str, camera_config: Dict) -> bool:
        """새 카메라 추가"""
        try:
            camera = Camera(camera_id, camera_config)
            self.cameras[camera_id] = camera
            self.logger.info(f"새 카메라 {camera_config['name']} 추가됨")
            return True
        except Exception as e:
            self.logger.error(f"카메라 추가 실패: {e}")
            return False
    
    def remove_camera(self, camera_id: str):
        """카메라 제거"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            self.logger.info(f"카메라 {camera_id} 제거됨")
    
    def restart_camera(self, camera_id: str) -> bool:
        """특정 카메라 재시작"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            time.sleep(1)  # 잠시 대기
            return self.cameras[camera_id].start()
        return False

# 전역 카메라 매니저 인스턴스
camera_manager = CameraManager()
