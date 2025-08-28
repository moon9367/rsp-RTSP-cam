#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Dict, List

class Config:
    """라즈베리파이 RTSP 웹캠 설정 클래스"""
    
    def __init__(self):
        # 웹캠 설정
        self.cameras = {
            'camera1': {
                'name': '웹캠 1',
                'device': '/dev/video0',
                'resolution': (640, 480),
                'fps': 30,
                'rtsp_port': 8554,
                'rtsp_path': '/camera1',
                'enabled': True
            },
            'camera2': {
                'name': '웹캠 2', 
                'device': '/dev/video1',
                'resolution': (640, 480),
                'fps': 30,
                'rtsp_port': 8555,
                'rtsp_path': '/camera2',
                'enabled': True
            },
            'camera3': {
                'name': '웹캠 3',
                'device': '/dev/video2',
                'resolution': (640, 480),
                'fps': 30,
                'rtsp_port': 8556,
                'rtsp_path': '/camera3',
                'enabled': True
            },
            'camera4': {
                'name': '웹캠 4',
                'device': '/dev/video3',
                'resolution': (640, 480),
                'fps': 30,
                'rtsp_port': 8557,
                'rtsp_path': '/camera4',
                'enabled': True
            }
        }
        
        # RTSP 서버 설정
        self.rtsp_server = {
            'host': '0.0.0.0',
            'base_port': 8554,
            'max_clients': 10,
            'buffer_size': 1024 * 1024,  # 1MB
            'timeout': 30
        }
        
        # 웹 인터페이스 설정
        self.web_interface = {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False
        }
        
        # 로깅 설정
        self.logging = {
            'level': 'INFO',
            'file': '/var/log/rtsp_cameras.log',
            'max_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        }
    
    def get_camera_config(self, camera_id: str) -> Dict:
        """특정 카메라 설정 반환"""
        return self.cameras.get(camera_id, {})
    
    def get_enabled_cameras(self) -> List[str]:
        """활성화된 카메라 목록 반환"""
        return [cam_id for cam_id, config in self.cameras.items() 
                if config.get('enabled', False)]
    
    def update_camera_config(self, camera_id: str, **kwargs):
        """카메라 설정 업데이트"""
        if camera_id in self.cameras:
            self.cameras[camera_id].update(kwargs)
    
    def save_config(self, filename: str = 'config.json'):
        """설정을 JSON 파일로 저장"""
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'cameras': self.cameras,
                'rtsp_server': self.rtsp_server,
                'web_interface': self.web_interface,
                'logging': self.logging
            }, f, indent=2, ensure_ascii=False)
    
    def load_config(self, filename: str = 'config.json'):
        """JSON 파일에서 설정 로드"""
        import json
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cameras = data.get('cameras', self.cameras)
                self.rtsp_server = data.get('rtsp_server', self.rtsp_server)
                self.web_interface = data.get('web_interface', self.web_interface)
                self.logging = data.get('logging', self.logging)
        except FileNotFoundError:
            print(f"설정 파일 {filename}을 찾을 수 없습니다. 기본 설정을 사용합니다.")

# 전역 설정 인스턴스
config = Config()
