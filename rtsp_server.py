#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import threading
import time
import logging
import socket
import struct
from typing import Dict, Optional, List
from camera_manager import camera_manager
from config import config

class RTSPStream:
    """개별 RTSP 스트림을 관리하는 클래스"""
    
    def __init__(self, camera_id: str, rtsp_config: Dict):
        self.camera_id = camera_id
        self.config = rtsp_config
        self.is_streaming = False
        self.clients: List[socket.socket] = []
        self.stream_thread = None
        self.logger = logging.getLogger(f"RTSPStream_{camera_id}")
        
        # RTSP 서버 소켓
        self.server_socket = None
        self.port = rtsp_config.get('rtsp_port', 8554)
        
    def start(self) -> bool:
        """RTSP 스트림 시작"""
        try:
            # RTSP 서버 소켓 생성
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.is_streaming = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            self.logger.info(f"RTSP 스트림 {self.camera_id} 시작됨 (포트: {self.port})")
            return True
            
        except Exception as e:
            self.logger.error(f"RTSP 스트림 시작 실패: {e}")
            return False
    
    def stop(self):
        """RTSP 스트림 중지"""
        self.is_streaming = False
        
        # 클라이언트 연결 종료
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # 스트림 스레드 종료 대기
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        self.logger.info(f"RTSP 스트림 {self.camera_id} 중지됨")
    
    def _stream_loop(self):
        """RTSP 스트리밍 메인 루프"""
        while self.is_streaming:
            try:
                # 클라이언트 연결 수락
                client_socket, addr = self.server_socket.accept()
                self.logger.info(f"클라이언트 연결됨: {addr}")
                
                # 클라이언트 스레드 시작
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_streaming:
                    self.logger.error(f"클라이언트 연결 오류: {e}")
                break
    
    def _handle_client(self, client_socket: socket.socket, addr):
        """클라이언트 연결 처리"""
        try:
            # RTSP 핸드셰이크
            if not self._rtsp_handshake(client_socket):
                return
            
            # 클라이언트 목록에 추가
            self.clients.append(client_socket)
            
            # RTP 스트리밍 시작
            self._rtp_stream(client_socket)
            
        except Exception as e:
            self.logger.error(f"클라이언트 처리 오류: {e}")
        finally:
            # 클라이언트 정리
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
            self.logger.info(f"클라이언트 연결 종료: {addr}")
    
    def _rtsp_handshake(self, client_socket: socket.socket) -> bool:
        """RTSP 핸드셰이크 수행"""
        try:
            # RTSP 요청 수신
            request = client_socket.recv(1024).decode('utf-8')
            if not request:
                return False
            
            # OPTIONS 요청에 대한 응답
            if 'OPTIONS' in request:
                response = (
                    'RTSP/1.0 200 OK\r\n'
                    'CSeq: 1\r\n'
                    'Public: DESCRIBE, SETUP, PLAY, PAUSE, TEARDOWN\r\n'
                    '\r\n'
                )
                client_socket.send(response.encode('utf-8'))
            
            # DESCRIBE 요청에 대한 응답
            elif 'DESCRIBE' in request:
                sdp = self._generate_sdp()
                response = (
                    'RTSP/1.0 200 OK\r\n'
                    'CSeq: 2\r\n'
                    'Content-Type: application/sdp\r\n'
                    f'Content-Length: {len(sdp)}\r\n'
                    '\r\n'
                    f'{sdp}'
                )
                client_socket.send(response.encode('utf-8'))
            
            # SETUP 요청에 대한 응답
            elif 'SETUP' in request:
                response = (
                    'RTSP/1.0 200 OK\r\n'
                    'CSeq: 3\r\n'
                    'Transport: RTP/AVP;unicast;client_port=8000-8001;server_port=8002-8003\r\n'
                    'Session: 12345678\r\n'
                    '\r\n'
                )
                client_socket.send(response.encode('utf-8'))
            
            # PLAY 요청에 대한 응답
            elif 'PLAY' in request:
                response = (
                    'RTSP/1.0 200 OK\r\n'
                    'CSeq: 4\r\n'
                    'Session: 12345678\r\n'
                    'Range: npt=0.000-\r\n'
                    '\r\n'
                )
                client_socket.send(response.encode('utf-8'))
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"RTSP 핸드셰이크 실패: {e}")
            return False
    
    def _generate_sdp(self) -> str:
        """SDP (Session Description Protocol) 생성"""
        camera_config = config.get_camera_config(self.camera_id)
        width, height = camera_config['resolution']
        fps = camera_config['fps']
        
        sdp = (
            'v=0\r\n'
            f'o=- 0 0 IN IP4 127.0.0.1\r\n'
            's=RTSP Camera Stream\r\n'
            'c=IN IP4 0.0.0.0\r\n'
            't=0 0\r\n'
            f'm=video 0 RTP/AVP 96\r\n'
            'a=rtpmap:96 H264/90000\r\n'
            f'a=framerate:{fps}\r\n'
            f'a=resolution:{width}x{height}\r\n'
        )
        return sdp
    
    def _rtp_stream(self, client_socket: socket.socket):
        """RTP 스트리밍 수행"""
        try:
            while self.is_streaming and client_socket in self.clients:
                # 카메라에서 프레임 가져오기
                frame = camera_manager.get_camera_frame(self.camera_id)
                if frame is None:
                    time.sleep(0.033)  # 30 FPS
                    continue
                
                # 프레임을 JPEG로 인코딩
                ret, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue
                
                # RTP 패킷 생성 및 전송
                rtp_packet = self._create_rtp_packet(jpeg_data.tobytes())
                try:
                    client_socket.send(rtp_packet)
                except:
                    break
                
                time.sleep(0.033)  # 30 FPS
                
        except Exception as e:
            self.logger.error(f"RTP 스트리밍 오류: {e}")
    
    def _create_rtp_packet(self, payload: bytes) -> bytes:
        """RTP 패킷 생성"""
        # RTP 헤더 (12바이트)
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        payload_type = 96  # JPEG
        
        # 시퀀스 번호와 타임스탬프는 간단하게 처리
        sequence_number = 0
        timestamp = int(time.time() * 90000)  # 90kHz 클럭
        ssrc = 0x12345678
        
        # RTP 헤더 구성
        first_byte = (version << 6) | (padding << 5) | (extension << 4) | cc
        second_byte = (marker << 7) | payload_type
        
        header = struct.pack('!BBHII', first_byte, second_byte, sequence_number, timestamp, ssrc)
        
        return header + payload
    
    def get_status(self) -> Dict:
        """스트림 상태 정보 반환"""
        return {
            'camera_id': self.camera_id,
            'port': self.port,
            'is_streaming': self.is_streaming,
            'client_count': len(self.clients),
            'rtsp_url': f"rtsp://localhost:{self.port}{self.config.get('rtsp_path', '')}"
        }

class RTSPServer:
    """RTSP 서버 메인 클래스"""
    
    def __init__(self):
        self.streams: Dict[str, RTSPStream] = {}
        self.is_running = False
        self.logger = logging.getLogger("RTSPServer")
        
    def start(self) -> bool:
        """RTSP 서버 시작"""
        try:
            # 활성화된 카메라들에 대해 RTSP 스트림 시작
            for camera_id in config.get_enabled_cameras():
                camera_config = config.get_camera_config(camera_id)
                stream = RTSPStream(camera_id, camera_config)
                if stream.start():
                    self.streams[camera_id] = stream
            
            self.is_running = len(self.streams) > 0
            self.logger.info(f"RTSP 서버 시작됨 - {len(self.streams)}개 스트림")
            return self.is_running
            
        except Exception as e:
            self.logger.error(f"RTSP 서버 시작 실패: {e}")
            return False
    
    def stop(self):
        """RTSP 서버 중지"""
        for stream in self.streams.values():
            stream.stop()
        self.streams.clear()
        self.is_running = False
        self.logger.info("RTSP 서버 중지됨")
    
    def start_stream(self, camera_id: str) -> bool:
        """특정 카메라의 RTSP 스트림 시작"""
        if camera_id in self.streams:
            return True
        
        camera_config = config.get_camera_config(camera_id)
        if not camera_config:
            return False
        
        stream = RTSPStream(camera_id, camera_config)
        if stream.start():
            self.streams[camera_id] = stream
            return True
        return False
    
    def stop_stream(self, camera_id: str):
        """특정 카메라의 RTSP 스트림 중지"""
        if camera_id in self.streams:
            self.streams[camera_id].stop()
            del self.streams[camera_id]
    
    def get_stream_status(self, camera_id: str) -> Optional[Dict]:
        """특정 스트림 상태 반환"""
        if camera_id in self.streams:
            return self.streams[camera_id].get_status()
        return None
    
    def get_all_status(self) -> Dict[str, Dict]:
        """모든 스트림 상태 반환"""
        status = {}
        for camera_id, stream in self.streams.items():
            status[camera_id] = stream.get_status()
        return status
    
    def get_rtsp_urls(self) -> Dict[str, str]:
        """모든 RTSP URL 반환"""
        urls = {}
        for camera_id, stream in self.streams.items():
            status = stream.get_status()
            urls[camera_id] = status['rtsp_url']
        return urls

# 전역 RTSP 서버 인스턴스
rtsp_server = RTSPServer()
