#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
import sys

def test_camera(device_path, camera_name):
    """개별 카메라 테스트"""
    print(f"\n🔍 {camera_name} 테스트 중... ({device_path})")
    
    # 카메라 열기
    cap = cv2.VideoCapture(device_path)
    
    if not cap.isOpened():
        print(f"❌ {camera_name}를 열 수 없습니다.")
        return False
    
    # 카메라 정보 출력
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    
    print(f"   해상도: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   코덱: {chr(fourcc & 0xFF)}{chr((fourcc >> 8) & 0xFF)}{chr((fourcc >> 16) & 0xFF)}{chr((fourcc >> 24) & 0xFF)}")
    
    # 설정 적용
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    
    # 프레임 읽기 테스트
    success_count = 0
    total_count = 10
    
    print(f"   프레임 읽기 테스트 중... ({total_count}회)")
    
    for i in range(total_count):
        ret, frame = cap.read()
        if ret:
            success_count += 1
            print(f"   ✓ 프레임 {i+1}: {frame.shape}")
        else:
            print(f"   ✗ 프레임 {i+1}: 읽기 실패")
        time.sleep(0.1)
    
    # 결과 출력
    success_rate = (success_count / total_count) * 100
    print(f"   📊 성공률: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print(f"   ✅ {camera_name} 정상 작동")
        result = True
    else:
        print(f"   ❌ {camera_name} 문제 발생")
        result = False
    
    # 카메라 해제
    cap.release()
    return result

def main():
    """메인 함수"""
    print("============================================================")
    print("🔴 카메라 테스트 스크립트")
    print("============================================================")
    
    # 테스트할 카메라 목록
    cameras = [
        ('/dev/video0', 'Arducam 1'),
        ('/dev/video4', 'Arducam 2'),
        ('/dev/video8', 'Arducam 3'),
        ('/dev/video12', 'Arducam 4')
    ]
    
    results = []
    
    for device_path, camera_name in cameras:
        result = test_camera(device_path, camera_name)
        results.append((camera_name, result))
    
    # 전체 결과 요약
    print("\n============================================================")
    print("📊 테스트 결과 요약")
    print("============================================================")
    
    working_cameras = sum(1 for _, result in results if result)
    total_cameras = len(results)
    
    for camera_name, result in results:
        status = "✅ 정상" if result else "❌ 문제"
        print(f"{camera_name}: {status}")
    
    print(f"\n전체 결과: {working_cameras}/{total_cameras} 카메라 정상 작동")
    
    if working_cameras == total_cameras:
        print("🎉 모든 카메라가 정상적으로 작동합니다!")
        return 0
    else:
        print("⚠️ 일부 카메라에 문제가 있습니다.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
