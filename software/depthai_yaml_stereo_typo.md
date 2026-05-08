# depthai yaml stereo 섹션 오타로 파라미터 미적용

## 환경

- OS: Ubuntu 24.04
- ROS2: Jazzy
- 카메라: OAK-D Pro (TurtleBot4 내장)
- 드라이버: depthai_ros_driver
- 설정 파일: oakd_pro.yaml

## 문제 상황

oakd_pro.yaml에서 stereo 섹션을 `streo:`로 잘못 작성했다.
stereo 토픽은 정상 발행되어 문제를 인지하기 어려웠으나, stereo 섹션의 파라미터가 적용되지 않은 상태였다.

```yaml
# 잘못된 설정
streo:            # ← 오타
  i_fps: 30.0
  i_align_depth: true
```

## 원인

YAML 파서는 `streo:`를 `stereo:`와 다른 키로 취급한다.
depthai 드라이버가 stereo 파라미터를 읽을 때 `streo:` 하위 항목을 찾지 못하므로,
해당 섹션 전체가 무시되고 드라이버 내부 기본값으로 동작한다.

stereo 토픽 자체는 `i_pipeline_type: RGBD` 설정에 의해 기본으로 발행되므로
토픽 목록만 봐서는 문제를 알 수 없다.

## 진단 순서

```bash
# 파라미터가 실제로 적용됐는지 확인
ros2 param get /<로봇네임스페이스>/oakd stereo.i_fps
ros2 param get /<로봇네임스페이스>/oakd stereo.i_align_depth
```

**미적용 시 출력:**
```
Parameter not set        # i_fps — 드라이버에서 파라미터 자체가 등록 안 됨
Boolean value is: True   # i_align_depth — 기본값이 true라 우연히 일치, 문제 안 보임
```

`Parameter not set`은 파라미터가 ROS 파라미터 서버에 등록조차 되지 않았다는 의미다.
토픽이 나온다고 해서 yaml 설정이 적용된 게 아님을 주의해야 한다.

## 해결 방법

yaml 파일에서 오타 수정 후 드라이버 재시작.

```yaml
# 수정 후
stereo:           # streo → stereo
  i_fps: 30.0
  i_align_depth: true
```

수정 후 확인:
```bash
ros2 param get /<로봇네임스페이스>/oakd stereo.i_fps
# Double value is: 30.0
```

## 참고

- `i_align_depth` 기본값이 `true`여서 오타가 있어도 값이 맞게 나온다 — 기본값과 의도가 일치하는 파라미터는 오타로 인한 미적용을 발견하기 어렵다
- `i_pipeline_type: RGBD`이면 `stereo.i_publish_topic`을 명시하지 않아도 stereo 토픽이 발행된다 (기본 동작)
- yaml 최상단 네임스페이스(`/oakd:`)가 실제 노드 경로(`/<로봇네임스페이스>/oakd`)와 달라도 launch 파일이 네임스페이스를 보정하므로 정상 적용될 수 있다 — `ros2 param get`으로 실제 적용 여부를 직접 확인하는 것이 정확하다
