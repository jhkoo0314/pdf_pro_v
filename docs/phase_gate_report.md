# Phase Gate Report Template

프로젝트: Prescription Data Flow (PDF)  
작성일: YYYY-MM-DD  
작성자:  
검토자:

## 0) Gate 판정 기준
- `PASS`: 필수 테스트 100% 통과, 필수 실패 0건, 필수 산출물 누락 0건
- `CONDITIONAL_PASS`: 비필수 이슈만 존재, 시정계획 명시 시 다음 Phase 진행 가능
- `FAIL`: 필수 테스트 실패 또는 필수 산출물 누락

## 1) 공통 실행/검증 로그
### 1.1 환경 정보
- python:
- pip:
- os:
- run_id:
- seed:

### 1.2 공통 테스트 실행 결과
- [ ] `pytest -m unit`
- [ ] `pytest -m contract`
- [ ] `pytest -m integration`
- [ ] `pytest -m regression`
- [ ] `pytest -m e2e`
- [ ] `pytest -m smoke`

### 1.3 필수 산출물 생성 확인
- [ ] `data/outputs/rep_kpi_month.*`
- [ ] `data/outputs/rep_kpi_quarter.*`
- [ ] `data/outputs/rep_kpi_year.*`
- [ ] `data/outputs/kpi_summary_month.*`
- [ ] `data/outputs/kpi_summary_quarter.*`
- [ ] `data/outputs/kpi_summary_year.*`
- [ ] `data/outputs/validation_report.*`
- [ ] `data/outputs/tracking_report.*`

### 1.4 컬럼 표기(영문+한글 병행) 검증
- [ ] 문서/리포트/UI 표기 형식: `column_en (한글명)` 적용
- [ ] 라벨 매핑 누락 0건
- [ ] Streamlit 원본 컬럼 토글 동작 확인
- [ ] 다운로드 파일 2종(`*_raw`, `*_label`) 생성 확인

### 1.5 단계 정책 검증(MVP -> 2단계 -> 3단계)
- [ ] 1단계: overlap 생성 비활성화(0%)
- [ ] 1단계: 병합파일 기준 해석 가능 상태 검증 완료
- [ ] 2단계: overlap 유도 비율 목표 충족(20~30%)
- [ ] 3단계: Streamlit에서 share 수동 조정/확정 기능 동작 확인

## 2) Phase별 Gate 기록

## Phase 1 - Foundation & Contract
목표:
- 데이터 계약, 컬럼 계약, I/O 표준화 완료

실행 명령:
```bash
# 예시
pytest -m "unit or contract"
```

테스트 결과:
- unit:
- contract:
- 실패 건수:

핵심 검증 항목:
- [ ] 필수 컬럼 존재
- [ ] 컬럼 type/nullable 계약 충족
- [ ] UTF-8 정합성(`U+FFFD` 0건)

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 2 - Ingest & Mastering
목표:
- `generate_synth`, `ingest_merge`, `mastering` 안정화

실행 명령:
```bash
# 예시
pytest -m "unit or integration"
```

테스트 결과:
- unit:
- integration:
- 실패 건수:

핵심 검증 항목:
- [ ] `pharmacy_uid` 누락 0건
- [ ] `territory_code` 매핑 품질 기준 충족
- [ ] 동일 seed 재실행 본문 동일

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 3 - Tracking Validation
목표:
- `tracking_validation` 구현 및 `tracking_report` 발행

실행 명령:
```bash
# 예시
pytest -m "unit or contract or integration"
```

테스트 결과:
- unit:
- contract:
- integration:
- 실패 건수:

핵심 검증 항목:
- [ ] `coverage_ratio`, `gap_amount`, `gap_ratio` 계산 정확성
- [ ] `data/outputs/tracking_report.*` 생성
- [ ] 미포착 케이스 분류/연결 가능

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 4 - Share Settlement
목표:
- 쉐어 배분/재배분/전분기 연장 로직 안정화

실행 명령:
```bash
# 예시
pytest -m "unit or regression"
```

테스트 결과:
- unit:
- regression:
- 실패 건수:

핵심 검증 항목:
- [ ] 보전성 `sum(amount_pre_share) == sum(amount_post_share)`
- [ ] 복수 의원 재배분(BaseAmount 비례)
- [ ] `share_rule_source` 정확성(`direct`/`extended`/`none`)
- [ ] 단계 정책 준수: 1단계 overlap=0, 2단계 overlap>0

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 5 - KPI Publish
목표:
- 월/분기/연 KPI 발행 및 요약 산출물 완성

실행 명령:
```bash
# 예시
pytest -m "contract or integration or e2e"
```

테스트 결과:
- contract:
- integration:
- e2e:
- 실패 건수:

핵심 검증 항목:
- [ ] KPI 출력 6종 생성
- [ ] 기간별 집계 일관성
- [ ] `data_quality_flag` 반영

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 6 - Validation & Trace
목표:
- validation 리포트와 trace 상태 전이 운영 루프 완성

실행 명령:
```bash
# 예시
pytest -m "unit or integration or regression"
```

테스트 결과:
- unit:
- integration:
- regression:
- 실패 건수:

핵심 검증 항목:
- [ ] `data/outputs/validation_report.*` 생성
- [ ] trace 상태 전이(`Unverified -> Inquired -> Confirmed/Rejected`)
- [ ] 실패 사유 누락 0건

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

---

## Phase 7 - Streamlit Smoke
목표:
- 추적 -> 쉐어 -> KPI 흐름 UI 검증

실행 명령:
```bash
# 예시
pytest -m smoke
```

테스트 결과:
- smoke:
- 실패 건수:

핵심 검증 항목:
- [ ] 주요 페이지 로딩
- [ ] 전역 필터 동작
- [ ] CSV/XLSX 다운로드 동작
- [ ] share 수동조정 및 확정(approve) 동작
- [ ] 확정 후 KPI 재반영 확인

게이트 판정: `PASS | CONDITIONAL_PASS | FAIL`  
이슈/조치:

## 3) 최종 Gate 요약
| Phase | 판정 | 필수 실패 건수 | 필수 산출물 누락 | 비고 |
|---|---|---:|---:|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |
| 6 |  |  |  |  |
| 7 |  |  |  |  |

최종 판정: `PASS | CONDITIONAL_PASS | FAIL`

컬럼 병행표기 최종 판정: `PASS | CONDITIONAL_PASS | FAIL`

## 4) 승인
- 작성자:
- 검토자:
- 승인일:
