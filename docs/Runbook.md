# Runbook - Prescription Data Flow (MVP Rebuild)

## 0) 목적
이 문서는 운영 관점에서 PDF 파이프라인을 실행/점검/판정하는 표준 절차다.  
핵심 흐름은 `병합 -> 마스터링 -> 추적검증 -> 쉐어정산 -> KPI 발행 -> Validation/Trace` 순서로 고정한다.

## 1) 운영 전 점검
1. Python/의존성 확인
   - `python -V`
   - `python -m pip -V`
2. 입력 파일 확인(`data/raw`)
   - 병원 원천: `1.*.xlsx`
   - 약국 원천: `2.*.xlsx`
   - 도매 원천: `*.csv`
3. 인코딩 점검
   - 텍스트 파일 UTF-8 유지
   - `U+FFFD`(replacement char) 유입 금지

## 2) 표준 실행 절차 (CLI)
1. 차원/병합 생성
   - `python -m src.generate_synth --seed 42 --valid-from 2026-01-01 --output-dir data/raw`
   - `python -m src.ingest_merge --raw-dir data/raw --output-dir data/raw --seed 42`
2. 마스터링
   - `python -m src.mastering --raw-dir data/raw --output-dir data/outputs --seed 42 --territory-missing-threshold 0.05`
3. 추적 검증
   - `python -m src.tracking_validation --input-dir data/outputs --output-dir data/outputs --min-coverage 0.75`
4. 쉐어 정산
   - `python -m src.share_engine --input-dir data/outputs --output-dir data/outputs`
5. KPI 발행
   - `python -m src.kpi_publish --input-dir data/outputs --output-dir data/outputs`
6. 검증/트레이스
   - `python -m src.validation --input-dir data/outputs --output-dir data/outputs`
   - `python -m src.trace_log --input-dir data/outputs --output-dir data/outputs`

## 3) Streamlit 운영 절차
1. 앱 실행
   - `streamlit run app/streamlit_app.py`
2. 사이드바 `MVP1 전체 파이프라인 실행` 버튼 실행
3. 탭별 점검
   - `처방추적 검증`: coverage/gap 확인
   - `중첩구간 쉐어 정산`: MVP1은 overlap OFF 상태 확인
   - `월/분기/연간 KPI 발행`: pre/post KPI 및 data_quality_flag 확인
   - `Validation & Trace 운영`: 이슈/상태전이 로그 확인

## 4) 산출물 점검 체크리스트
필수 출력(`data/outputs`)
1. `tracking_report_label.*`
2. `share_settlement_label.*`
3. `rep_kpi_month|quarter|year_label.*`
4. `kpi_summary_month|quarter|year_label.*`
5. `validation_report_label.*`
6. `trace_log_label.*`, `trace_history_label.*`

필수 조건
1. `pharmacy_uid` 누락 0건
2. `share_rule_source` 허용값(`direct/extended/none`) 외 0건
3. 보전성 위배 0건 (`sum(amount_pre_share) == sum(amount_post_share)`)
4. `data_quality_flag` 생성 및 상태 확인

## 5) 장애 대응
1. `ModuleNotFoundError: src`
   - Streamlit 앱 경로 실행 위치 점검
   - `app/streamlit_app.py` 내 프로젝트 루트 path 주입 여부 확인
2. 한글 깨짐
   - 파일 저장 인코딩 UTF-8로 재저장
   - 콘솔 깨짐과 파일 깨짐 구분(파일은 Python으로 확인)
3. 출력 누락
   - 상위 단계 산출물 존재 확인 후 재실행
   - `tracking -> share -> kpi -> validation -> trace` 순서 유지

## 6) 단계별 운영 기준
## 6.1 MVP 1단계 (완료 상태 기준)
1. overlap 생성 OFF
2. 병합 결과 해석 가능
3. 추적/쉐어/KPI/validation/trace 산출물 생성
4. Streamlit에서 필터/조회/다운로드 동작

## 6.2 Phase 2 (중첩구간 유도 + Share 고도화)
1. overlap ON 데이터 생성
2. 중첩구간별 정산 및 감사 로그(`share_overlap_audit`) 생성
3. 전분기 연장 + 중첩 동시 시나리오 검증

## 6.3 Phase 3 완료 기준 (업로드 자동화 + 수동 확정)
완료 판정은 아래 5개를 모두 충족해야 한다.
1. **파일 업로드 자동화**
   - 사용자가 병원/약국/도매 원천 파일 업로드 시, 사전 수작업 없이 백엔드 파이프라인 자동 실행
2. **자동 검증/오류 피드백**
   - 스키마/인코딩/필수 컬럼 오류를 UI에서 즉시 표시
3. **수동 조정 및 확정**
   - Streamlit에서 share 값 직접 조정 가능
   - 확정 시 `version`, `status`, `approved_by`, `approved_at` 저장
4. **재반영 일관성**
   - 확정 후 KPI 재발행 시 pre/post 집계 일관성 유지
5. **운영 추적성**
   - 확정 이력과 trace 상태전이 로그가 함께 남고, 다운로드 가능

## 7) 권장 테스트 실행
1. `pytest -m unit`
2. `pytest -m contract`
3. `pytest -m integration`
4. `pytest -m regression`
5. `pytest -m e2e`
6. `pytest -m smoke`

## 8) 변경 이력 관리
1. 스키마/룰/화면 변경 시 문서 동시 업데이트
2. TODO 체크 상태와 실제 테스트 결과 일치 유지
3. Phase Gate 판정 시 근거 파일 경로를 기록
