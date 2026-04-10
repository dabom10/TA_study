# 가상환경 개념 및 Docker vs Anaconda 비교

## 한 줄 요약

가상환경 = 프로젝트마다 독립된 패키지 공간. Docker는 OS 레벨까지, Anaconda는 Python 패키지 레벨만 격리.

## 핵심 내용

### 가상환경이 필요한 이유

Python은 같은 패키지를 두 버전 동시에 설치할 수 없다.

```
프로젝트 A → torch 1.x 필요
프로젝트 B → torch 2.x 필요  ← 전역 설치 시 충돌
```

가상환경을 쓰면 프로젝트마다 독립된 패키지 공간을 가진다.

```
[내 컴퓨터]
  Python 3.10 (global)
    ├─ [env_A]  torch 1.x, numpy 1.x
    └─ [env_B]  torch 2.x, numpy 2.x
```

### Anaconda (conda/virtualenv)

- Python 패키지·인터프리터만 격리
- OS 라이브러리(`glibc`, `libstdc++` 등)는 호스트 것 그대로 사용
- OS가 달라지면 동작 보장 안 됨

```
Host OS
  └─ Host Kernel
       └─ [conda env A] Python 3.9 + numpy 1.x
       └─ [conda env B] Python 3.11 + torch 2.x
```

### Docker

- OS 유저스페이스 전체(패키지 + 시스템 라이브러리 + 환경변수 + 파일시스템)를 컨테이너 안에 묶음
- 커널만 호스트와 공유 (VM처럼 커널까지 가상화하지 않음)
- 어느 환경에서 실행해도 동일한 동작 보장

```
Host OS
  └─ Host Kernel  ← 이것만 공유
       └─ [Container A] Ubuntu 20.04 + Python 3.9 + numpy + libfoo.so.2
       └─ [Container B] Debian 11   + Python 3.11 + torch + libbar.so.5
```

### Docker OS 격리 메커니즘

| 기능 | 역할 |
|------|------|
| **namespace** | 프로세스·네트워크·파일시스템 등을 컨테이너마다 독립 공간으로 분리 |
| **cgroup** | CPU·메모리 등 자원 사용량을 컨테이너 단위로 제한 |

### 비교 요약

| | 격리 범위 | OS 의존성 |
|---|---|---|
| **Anaconda** | Python 패키지만 | 호스트 OS에 종속 |
| **Docker** | OS 유저스페이스 전체 | 컨테이너 내부에서 완전히 해결 |

## 출처

- [Python Virtual Environments: A Primer – Real Python](https://realpython.com/python-virtual-environments-a-primer/)
- [venv — Python 공식 문서](https://docs.python.org/3/library/venv.html)
- [Virtual Environments vs. Containers: A Beginner's Guide](https://data-intelligence.hashnode.dev/navigating-machinedeep-learning-environments-virtual-environments-vs-containers)
- [Running Python/R with Docker vs. Virtual Environment](https://medium.com/@rami.krispin/running-python-r-with-docker-vs-virtual-environment-4a62ed36900f)
- [Using Conda? You might not need Docker](https://pythonspeed.com/articles/conda-vs-docker/)
