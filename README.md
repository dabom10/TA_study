# TA_study notes

TA 업무 중 발생한 문제와 해결 방법, 알게 된 정보들을 기록합니다.

## 디렉토리 구조

```
TA_study/
├── README.md
├── env/        # 환경 세팅 (Ubuntu, ROS2, CUDA 등)
├── hardware/   # 하드웨어 (로봇, 카메라, 센서)
├── software/   # 코드/패키지 에러
├── network/    # 네트워크/통신
└── tips/       # 유용한 명령어 및 팁
```

---

## 문제 목록

| 날짜 | 분류 | 문제 요약 | 파일 |
|------|------|-----------|------|
| 2026-03-30 | env | NVIDIA 드라이버 설치 후 HDMI 외장 모니터 블랙스크린 | [nvidia_hdmi_troubleshooting.md](env/nvidia_hdmi_troubleshooting.md) |
| 2026-03-30 | tips | apt vs apt-get 차이 | [apt-vs-apt-get.md](tips/apt-vs-apt-get.md) |
| 2026-03-31 | tips | 시스템 설정 및 자주 쓰는 명령어 모음 | [command.md](tips/command.md) |
| 2026-03-31 | network | configure_discovery.sh 실행 시 아무 동작 없이 종료 (인터넷 차단 네트워크에서 wget 실패) | [configure_discovery_wget_fail.md](network/configure_discovery_wget_fail.md) |
