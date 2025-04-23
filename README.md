# Library Data Agent

공연 데이터 수집 및 분석을 위한 AI 기반 데이터 에이전트 시스템입니다.

## 주요 기능

### 데이터 관리
- 공연 정보 관리
  - 공연 기본 정보 등록/수정/삭제
  - 공연별 매출 현황 및 통계 분석
  - 공연별 마케팅 캘린더 관리
- 배우 정보 관리
  - 배우 프로필 등록/수정/삭제
  - 출연 이력 관리
- 캐스팅 관리
  - 공연별 캐스팅 일정 관리
  - 배우별 출연 일정 관리
- 좌석 등급 관리
  - 공연장별 좌석 등급 설정
  - 등급별 가격 관리
- 리뷰 관리
  - 공연 리뷰 수집 및 관리
  - 리뷰 감성 분석

### 대시보드
- 실시간 통계 현황
  - 총 판매액, 관객수, 객석 점유율
  - 진행중인 공연 현황
- 데이터 시각화
  - 월별 판매 추이 차트
  - 장르별 판매 비율 차트
- 공연 목록
  - 진행중인 공연 목록 제공
  - 판매액/관객수/점유율 기준 정렬
  - 장르별 필터링

## 기술 스택

### 백엔드
- Python 3.9+
- Django 4.2
- SQLAlchemy
- BeautifulSoup4

### 프론트엔드
- Bootstrap 5.3.0
- Chart.js 4.4.1
- Bootstrap Icons

### 데이터베이스
- SQLite (개발)
- PostgreSQL (배포)

### 클라우드 서비스 (GCP)
- App Engine: 애플리케이션 호스팅
- Cloud SQL: PostgreSQL 데이터베이스 관리
- Cloud Storage: 정적/미디어 파일 저장
- Cloud Build: 자동 배포 파이프라인
- Cloud Logging: 애플리케이션 로그 관리
- Cloud Monitoring: 성능 모니터링

## 시스템 요구사항

### 필수 요구사항
- Python 3.9 이상
- pip (Python 패키지 관리자)
- 가상환경 (venv)

## 설치 및 실행

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
.\venv\Scripts\activate   # Windows
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

4. 개발 서버 실행
```bash
python manage.py runserver
```

## 최근 업데이트 내용

### 2025-04-23
- 모든 대시보드(공연/전시/뮤지컬/연극)의 통계 카드에 '전월대비' 표시 추가
- 통계 카드 레이아웃 및 디자인 개선
- 차트 섹션 레이아웃 정리
- 성능 목록 테이블 스타일 개선