# Prescription Data Flow (PDF) - MVP Rebuild

이 프로젝트는 `도매 출하 -> 문전약국 -> 병원/담당자` 흐름을 추적하고,  
그 결과를 `검증 -> 쉐어 정산 -> KPI 발행`으로 연결하는 운영형 데이터 파이프라인입니다.

## 1. 현재 상태 (2026-03-04)
- MVP 1단계 완료
  - 병합/마스터링/추적/쉐어(중첩 OFF)/KPI/Validation/Trace 산출물 생성
  - Streamlit 오케스트레이션 UI 구현
  - 영문+한글 병행 컬럼(`*_label`) 기반 표시
- 중첩구간 정산(Phase 2) 및 Streamlit 수동 확정(Phase 3)은 계획 단계

## 2. 핵심 원칙
- KPI 금액 기준: `amount_ship`
- 기간 기준: `year_month`, `year_quarter`, `year`
- 권역 기준: `territory_code`
- 쉐어 정산 그레인: `year_quarter x territory_code x brand`
- Validation First:
  - `generate/ingest -> mastering -> tracking_validation -> share_settlement -> kpi_publish -> validation -> trace_log`

## 3. 디렉터리
- `src/`: 비즈니스 로직
- `app/streamlit_app.py`: UI 오케스트레이션
- `data/raw`: 원천 + 생성 raw
- `data/outputs`: 마스터/추적/쉐어/KPI/검증 산출물
- `docs/`: PRD, Runbook, TODO, 데이터 사전

## 4. 실행 방법
## 4.1 전체 파이프라인 (CLI)
```powershell
python -m src.generate_synth --seed 42 --valid-from 2026-01-01 --output-dir data/raw
python -m src.ingest_merge --raw-dir data/raw --output-dir data/raw --seed 42
python -m src.mastering --raw-dir data/raw --output-dir data/outputs --seed 42 --territory-missing-threshold 0.05
python -m src.tracking_validation --input-dir data/outputs --output-dir data/outputs --min-coverage 0.75
python -m src.share_engine --input-dir data/outputs --output-dir data/outputs
python -m src.kpi_publish --input-dir data/outputs --output-dir data/outputs
python -m src.validation --input-dir data/outputs --output-dir data/outputs
python -m src.trace_log --input-dir data/outputs --output-dir data/outputs
```

## 4.2 Streamlit
```powershell
streamlit run app/streamlit_app.py
```

화면에서 `MVP1 전체 파이프라인 실행` 버튼으로 동일 흐름을 실행할 수 있습니다.

## 5. 현재 산출물 (주요)
- `data/raw/fact_ship_pharmacy_raw_label.*`
- `data/outputs/fact_ship_pharmacy_mastered_label.*`
- `data/outputs/tracking_report_label.*`
- `data/outputs/share_settlement_label.*`
- `data/outputs/rep_kpi_month|quarter|year_label.*`
- `data/outputs/kpi_summary_month|quarter|year_label.*`
- `data/outputs/validation_report_label.*`
- `data/outputs/trace_log_label.*`

## 6. 데이터/표시 정책
- 저장 포맷: parquet + csv
- 컬럼 표기: 기본 `영문(한글)` 병행 헤더 (`*_label`)
- Streamlit 표기 금액: 천원 단위(표시 전용 변환)
- 원본 수치(할인율/소수 포함)는 raw/output 파일에 그대로 유지

## 7. 제품 로드맵 (중요)
## Phase 2 - 중첩구간 유도 + Share 고도화
- overlap 생성 ON
- 중첩 pool/재배분/감사 로그(`share_overlap_audit`) 고도화
- 룰 해소 경로(`direct/extended/overlap_resolved/none`) 명시

## Phase 3 - Streamlit 수동 확정 + 파일 업로드 자동화
- 목표:
  - 사용자가 원천 파일을 업로드하면 백엔드가 병합/마스터링/추적/정산/KPI를 자동 실행
  - UI에서 share 값을 직접 조정 후 확정
- 예정 기능:
  - 업로드 입력: 병원/약국/도매 원천 파일
  - 자동 스키마 검사/인코딩 검사/컬럼 매핑
  - 실패 사유 즉시 표시(validation UI 연동)
  - 수동 확정 메타 저장:
    - `version`, `status`, `approved_by`, `approved_at`

## Phase 4 - 최종 목표
- 사전 수작업 없이 파일 업로드만으로 최종 결과 자동 생성
- 운영형 워크플로우 완성:
  - 업로드 -> 자동 병합 -> 정산 -> 검증 -> 리포트/다운로드

## 8. 테스트
```powershell
pytest -m unit
pytest -m contract
pytest -m integration
pytest -m regression
pytest -m e2e
pytest -m smoke
```

## 9. 참고 문서
- `docs/PRD.md`
- `docs/Runbook.md`
- `docs/TODO.md`
- `docs/01_business_rules.md`
- `docs/02_data_dictionary.md`
