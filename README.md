# naver_news_crawling-ver2
## Python을 이용한 네이버 뉴스 리스트 크롤링

Python으로 네이버 뉴스 검색 결과를 크롤링해 CSV로 저장하고, 생성된 CSV들을 분기별로 병합하는 스크립트입니다.

### 주요 기능
- **뉴스 크롤링**: 임의의 키워드와 기간(날짜 범위 또는 연도/분기)에 따라 네이버 뉴스 목록을 수집합니다.
- **동적 아이템 탐색**: UI가 자주 변하는 CSS 클래스 대신, `news.naver.com` 도메인의 기사 링크를 기반으로 헤드라인 앵커를 탐지해 안정적으로 아이템을 수집합니다.
- **수집 항목**: `제목`, `링크`, `신문사`, `날짜`, `본문 전문`(개별 기사 페이지에서 추출)
- **저장 형식**: 결과를 `out/naver_news_crawling_result/` 폴더에 `YYQ{분기}_{키워드}.csv`로 저장(예: `24Q1_윤리.csv`).
- **안전장치**: 사용자 에이전트 헤더 설정, 403 응답 시 재시도, 호출 간 랜덤 대기 적용.
- **중복 제거 및 정렬(병합 시)**: 병합 유틸리티로 같은 링크 중복 제거 후 날짜 기준 내림차순 정렬.

### 폴더 구조
- `main.py`: 네이버 뉴스 크롤러 실행 스크립트
- `merge_csv_by_quarter.py`: 크롤링 결과 CSV를 분기 단위로 병합하는 유틸리티
- `requirements.txt`: 의존성 목록
- `out/naver_news_crawling_result/`: 결과 CSV 출력 디렉터리(자동 생성)

### 요구 사항
- Python 3.8+
- 의존성 설치:
```bash
pip install -r requirements.txt
```

### 크롤러 동작 개요 (`main.py`)
- 네이버 검색 URL을 구성하여 페이지 단위로 목록을 가져옵니다.
- 목록 페이지에서는 `news.naver.com`으로 연결되는 기사 앵커(`a[href]`)들을 찾아 제목과 링크를 수집합니다. 불안정한 CSS 클래스 선택자는 사용하지 않습니다.
- 기사 링크로 접속해 본문을 `div.newsct_article._article_body`에서 추출합니다.
- 결과는 다음 열 순서로 CSV에 저장됩니다: `date, title, source, contents, link` (UTF-8-SIG 인코딩)
- 파일명은 시작일 기준 분기를 계산해 `YYQ{분기}_{키워드}.csv` 형식으로 저장됩니다.

참고: UI 변경 시에도 앵커 기반 탐색은 상대적으로 안정적입니다. 추가 필드(언론사/날짜)가 목록에 없다면 기사 페이지의 메타 태그를 우선적으로 활용할 수 있습니다.

### 사용 방법 — 크롤링 실행 (일반화된 CLI)
아래 플래그를 조합해 원하는 기간/키워드로 실행합니다.

- **필수**:
  - `--keywords`: 하나 이상 지정. 공백으로 여러 개 나열하거나 쉼표 구분 가능.
- **기간 지정(둘 중 하나)**:
  - `--start-date YYYY.MM.DD` 와 `--end-date YYYY.MM.DD`
  - 또는 `--year 2024 --quarter 1`
- **옵션**:
  - `--maxpage`: 페이지 수(페이지당 10건). 기본 `200`
  - `--result-path`: 결과 저장 경로. 기본 `out/naver_news_crawling_result/`
  - `--sleep-between`: 키워드 간 대기(초). 기본 `5.0`

예시:
```bash
# 1) 분기 기준, 여러 키워드 공백 구분
python main.py --year 2024 --quarter 1 --keywords 윤리 프라이버시 규제

# 2) 날짜 범위 기준, 쉼표로 키워드 나열
python main.py --start-date 2024.04.01 --end-date 2024.06.30 \
  --keywords 윤리,프라이버시,규제 --maxpage 100

# 3) 결과 저장 경로 지정
python main.py --year 2023 --quarter 4 --keywords AI \
  --result-path /absolute/path/to/out --sleep-between 3
```

주의: 정렬(sort) 옵션은 현재 고정값으로 동작하며, CLI 플래그는 비활성화되어 있습니다.

### 사용 방법 — CSV 병합 (`merge_csv_by_quarter.py`)
여러 키워드로 생성된 동일 분기의 CSV 파일들을 하나로 합칩니다. 같은 `link`를 기준으로 중복 제거하고, 날짜 내림차순으로 정렬합니다.

- 사용 가능한 분기 목록 보기:
```bash
python merge_csv_by_quarter.py --list --result-path out/naver_news_crawling_result/
```

- 연도/분기로 병합(권장: 크롤러의 파일명 규칙과 동일):
```bash
python merge_csv_by_quarter.py --year 2024 --quarter 1 --result-path out/naver_news_crawling_result/
```
생성 파일 예시: `out/naver_news_crawling_result/merged_24Q1_quarter.csv`

- 날짜 범위로 병합(레거시 파일명 패턴 대응):
```bash
python merge_csv_by_quarter.py \
  --start-date 24.01.01 \
  --end-date   24.03.31 \
  --result-path out/naver_news_crawling_result/
```
생성 파일 예시: `out/naver_news_crawling_result/merged_24.01.01_24.03.31_quarter.csv`

참고: 현재 크롤러의 파일명은 `YYQ{분기}_*.csv` 형식입니다. 일반적으로는 `--year/--quarter` 방식을 사용하세요.

### 주의 및 한계
- 네이버 페이지 구조가 변경되어도 앵커 기반 탐색은 비교적 안정적이지만, 기사 본문/메타 구조 변경 시 셀렉터 업데이트가 필요할 수 있습니다.
- 과도한 요청은 403 등 응답을 유발할 수 있습니다. 스크립트에 랜덤 지연과 재시도가 포함되어 있으나, 필요 시 대기 시간을 늘리세요.
- 서비스 약관과 로봇 배제 정책을 준수하고, 수집 데이터는 연구/개인적 용도로 합법적으로 사용하세요.

### 라이선스
프로젝트의 사용 조건이 별도로 명시되지 않았다면, 조직/프로젝트 정책에 따라 적용하세요.
