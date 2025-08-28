#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, jsonify, request, Response
import cv2
import numpy as np
import threading
import time
import logging
import json
from camera_manager import camera_manager
from rtsp_server import rtsp_server
from config import config

# Flask 앱 생성
app = Flask(__name__)

# CORS 설정 (flask_cors 없이)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """전체 시스템 상태 반환"""
    try:
        camera_status = camera_manager.get_all_status()
        rtsp_status = rtsp_server.get_all_status()
        
        status = {
            'system': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': time.time(),
                'cameras': len(camera_status),
                'rtsp_streams': len(rtsp_status)
            },
            'cameras': camera_status,
            'rtsp_streams': rtsp_status
        }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"상태 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/start', methods=['POST'])
def start_camera(camera_id):
    """특정 카메라 시작"""
    try:
        success = camera_manager.start_camera(camera_id)
        if success:
            # RTSP 스트림도 시작
            rtsp_server.start_stream(camera_id)
            return jsonify({'success': True, 'message': f'카메라 {camera_id} 시작됨'})
        else:
            return jsonify({'success': False, 'message': f'카메라 {camera_id} 시작 실패'}), 400
    except Exception as e:
        logger.error(f"카메라 시작 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/stop', methods=['POST'])
def stop_camera(camera_id):
    """특정 카메라 중지"""
    try:
        camera_manager.stop_camera(camera_id)
        rtsp_server.stop_stream(camera_id)
        return jsonify({'success': True, 'message': f'카메라 {camera_id} 중지됨'})
    except Exception as e:
        logger.error(f"카메라 중지 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/restart', methods=['POST'])
def restart_camera(camera_id):
    """특정 카메라 재시작"""
    try:
        success = camera_manager.restart_camera(camera_id)
        if success:
            return jsonify({'success': True, 'message': f'카메라 {camera_id} 재시작됨'})
        else:
            return jsonify({'success': False, 'message': f'카메라 {camera_id} 재시작 실패'}), 400
    except Exception as e:
        logger.error(f"카메라 재시작 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/start_all', methods=['POST'])
def start_all_cameras():
    """모든 카메라 시작"""
    try:
        success = camera_manager.start_all()
        if success:
            rtsp_server.start()
            return jsonify({'success': True, 'message': '모든 카메라 시작됨'})
        else:
            return jsonify({'success': False, 'message': '카메라 시작 실패'}), 400
    except Exception as e:
        logger.error(f"모든 카메라 시작 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/stop_all', methods=['POST'])
def stop_all_cameras():
    """모든 카메라 중지"""
    try:
        camera_manager.stop_all()
        rtsp_server.stop()
        return jsonify({'success': True, 'message': '모든 카메라 중지됨'})
    except Exception as e:
        logger.error(f"모든 카메라 중지 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rtsp/urls')
def get_rtsp_urls():
    """RTSP URL 목록 반환"""
    try:
        urls = rtsp_server.get_rtsp_urls()
        return jsonify({'success': True, 'urls': urls})
    except Exception as e:
        logger.error(f"RTSP URL 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def get_config():
    """현재 설정 반환"""
    try:
        config_data = {
            'cameras': config.cameras,
            'rtsp_server': config.rtsp_server,
            'web_interface': config.web_interface
        }
        return jsonify({'success': True, 'config': config_data})
    except Exception as e:
        logger.error(f"설정 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['PUT'])
def update_config():
    """설정 업데이트"""
    try:
        data = request.get_json()
        
        if 'cameras' in data:
            for camera_id, camera_config in data['cameras'].items():
                config.update_camera_config(camera_id, **camera_config)
        
        # 설정 파일 저장
        config.save_config()
        
        return jsonify({'success': True, 'message': '설정 업데이트됨'})
    except Exception as e:
        logger.error(f"설정 업데이트 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/snapshot')
def get_snapshot(camera_id):
    """카메라 스냅샷 반환"""
    try:
        frame = camera_manager.get_camera_frame(camera_id)
        if frame is None:
            return jsonify({'error': '프레임을 가져올 수 없습니다'}), 400
        
        # JPEG로 인코딩
        ret, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ret:
            return jsonify({'error': '이미지 인코딩 실패'}), 500
        
        # 응답 생성
        response = Response(jpeg_data.tobytes(), mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        logger.error(f"스냅샷 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cameras/<camera_id>/stream')
def get_stream(camera_id):
    """카메라 스트림 반환 (MJPEG)"""
    def generate_frames():
        while True:
            try:
                frame = camera_manager.get_camera_frame(camera_id)
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # JPEG로 인코딩
                ret, jpeg_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue
                
                # MJPEG 스트림 형식으로 전송
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data.tobytes() + b'\r\n')
                
                time.sleep(0.033)  # 30 FPS
                
            except Exception as e:
                logger.error(f"스트림 생성 오류: {e}")
                time.sleep(0.1)
    
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system/health')
def get_system_health():
    """시스템 상태 점검"""
    try:
        health = {
            'status': 'healthy',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'checks': {}
        }
        
        # 카메라 상태 점검
        camera_status = camera_manager.get_all_status()
        active_cameras = sum(1 for cam in camera_status.values() if cam['is_running'])
        health['checks']['cameras'] = {
            'total': len(camera_status),
            'active': active_cameras,
            'status': 'healthy' if active_cameras > 0 else 'warning'
        }
        
        # RTSP 스트림 상태 점검
        rtsp_status = rtsp_server.get_all_status()
        active_streams = sum(1 for stream in rtsp_status.values() if stream['is_streaming'])
        health['checks']['rtsp_streams'] = {
            'total': len(rtsp_status),
            'active': active_streams,
            'status': 'healthy' if active_streams > 0 else 'warning'
        }
        
        # 전체 상태 결정
        if any(check['status'] == 'warning' for check in health['checks'].values()):
            health['status'] = 'warning'
        
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"시스템 상태 점검 오류: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/system/logs')
def get_logs():
    """로그 조회"""
    try:
        # 간단한 로그 정보 반환 (실제로는 로그 파일에서 읽어와야 함)
        logs = {
            'recent_events': [
                {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'level': 'INFO', 'message': '웹 인터페이스 시작됨'},
                {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'level': 'INFO', 'message': '카메라 매니저 초기화됨'},
                {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'level': 'INFO', 'message': 'RTSP 서버 준비됨'}
            ]
        }
        return jsonify(logs)
    except Exception as e:
        logger.error(f"로그 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 설정 로드
    config.load_config()
    
    # 웹 인터페이스 설정
    host = config.web_interface['host']
    port = config.web_interface['port']
    debug = config.web_interface['debug']
    
    logger.info(f"웹 인터페이스 시작: http://{host}:{port}")
    
    # Flask 앱 실행
    app.run(host=host, port=port, debug=debug, threaded=True)
