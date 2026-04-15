# OpenCV 이미지 입출력 함수

## 한 줄 요약
imread(읽기) / imwrite(저장) / imshow(화면 표시) — OpenCV 이미지 입출력 3총사.

## 핵심 내용

### imwrite — 파일로 저장

```python
cv2.imwrite(파일경로, 이미지)
```

- 확장자에 따라 포맷 자동 결정 (`.jpg`, `.png` 등)
- 성공 시 `True`, 실패 시 `False` 반환

```python
cv2.imwrite("output.jpg", frame)
cv2.imwrite("output.png", frame)

# 실제 사용 예 (2_1_e)
file_name = os.path.join(save_directory, f"{prefix}_img_{count}.jpg")
cv2.imwrite(file_name, node.frame)
```

---

### imread — 파일에서 읽기

```python
frame = cv2.imread(파일경로)
frame = cv2.imread(파일경로, cv2.IMREAD_GRAYSCALE)  # 흑백으로 읽기
```

- 반환값은 numpy 배열 (BGR 포맷)
- 파일이 없으면 `None` 반환 → 로드 후 `if frame is None` 체크 필요

```python
frame = cv2.imread("image.jpg")
if frame is None:
    print("이미지 로드 실패")
```

---

### imshow — 화면에 표시 (저장 X)

```python
cv2.imshow("창 이름", frame)
cv2.waitKey(1)   # 필수: 이벤트 루프 처리 및 키 입력 대기 (ms)
```

- `waitKey(0)` — 키 입력 있을 때까지 무한 대기
- `waitKey(1)` — 1ms 대기 후 바로 넘어감 (실시간 스트리밍에 사용)
- 반환값 = 눌린 키의 ASCII 코드 (`ord('q')` 등과 비교)

```python
key = cv2.waitKey(1) & 0xFF
if key == ord('q'):
    break
```

---

### 3총사 비교

| 함수 | 방향 | 저장 여부 |
|------|------|-----------|
| `imread` | 파일 → numpy | X (읽기만) |
| `imwrite` | numpy → 파일 | O |
| `imshow` | numpy → 화면 | X (표시만) |

---

### 관련 함수

```python
cv2.destroyAllWindows()   # imshow로 연 모든 창 닫기
cv2.destroyWindow("창 이름")  # 특정 창만 닫기
```

## 다른 섹션과의 연결
- [cvbridge_and_ros2_image.md](cvbridge_and_ros2_image.md) — ROS2 메시지를 numpy로 변환 후 imwrite/imshow에 넘김
- `2_1_d`, `2_1_e` — imwrite로 학습 데이터 캡처
- `2_4_d` — imwrite로 탐지 결과 저장

## 의문점 / 나중에 파고들 것
- jpg vs png 저장 품질/용량 트레이드오프
- `imwrite` 품질 옵션: `cv2.imwrite("out.jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])`
