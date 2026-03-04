# PRD - Prescription Data Flow (Rebuild)

## 0. 문서 정보
- 문서명: Prescription Data Flow 제품 요구사항(PRD)
- 버전: v2.0 (Rebuild 기준)
- 기준일: 2026-03-04
- 범위: MVP 1단계 완료 + Phase 2/3/4 로드맵

## 1. 제품 정체성
우선순위:
1. 처방추적 시스템 구축 (Primary)
2. 실적 claim 검증 (Secondary)
3. 월/분기/연간 정산 및 KPI 발행 (Tertiary)

제품 정의:
- 단순 리포트 도구가 아니라 `도매 -> 문전약국 -> 병원/담당자` 흐름을 추적하고,
- 결과를 검증/정산/KPI 발행으로 연결하는 운영 시스템

## 2. 문제 정의
- 외부 처방데이터 구매비용이 높아 상시 운영에 불리
- 자사 출하/약국/병원/담당자 데이터 기반으로 대체 가능한 실무형 운영체계 필요

## 3. 목표
## 3.1 MVP 1단계 목표 (완료)
- 중첩구간 생성 없이(overlap OFF) 병합/해석/검증/정산/KPI 발행 가능
- Streamlit에서 추적 -> 쉐어 -> KPI -> Validation/Trace 조회 가능

## 3.2 다음 목표
- Phase 2: 중첩구간 유도 + Share 고도화
- Phase 3: Streamlit 업로드 자동화 + 수동 확정 + 재발행
- Phase 4: 파일 업로드만으로 최종 결과 자동 생성(무수작업)

## 4. 고정 운영 플로우
1. `ingest_merge` (병합 원천 로우 생성)
2. `mastering` (`pharmacy_uid`, `territory_code`)
3. `tracking_validation` (coverage/gap)
4. `share_settlement`
5. `kpi_publish`
6. `validation` + `trace_log`

## 5. 핵심 비즈니스 규칙
- KPI 금액 기준: `amount_ship`
- 날짜 기준: `ship_date`
- 기간 기준: `year_month`, `year_quarter`, `year`
- 권역 기준: `territory_code` (행정구역 아님)
- 쉐어 그레인: `year_quarter x territory_code x brand`
- 룰 누락 시 전분기 룰 연장(`extended`)
- 추적 시작 이전 기간 소급 귀속 금지

## 6. 데이터 계약
- 저장 포맷: parquet(primary), csv(secondary)
- 경로: `data/` 하위
- 라벨 파일: `*_label` (영문+한글 병행 헤더)

필수 산출물:
- `rep_kpi_month|quarter|year`
- `kpi_summary_month|quarter|year`
- `tracking_report`
- `validation_report`
- `trace_log`

## 7. 구현 모듈
- `src/generate_synth.py`
- `src/ingest_merge.py`
- `src/mastering.py`
- `src/tracking_validation.py`
- `src/share_engine.py`
- `src/kpi_publish.py`
- `src/validation.py`
- `src/trace_log.py`
- `app/streamlit_app.py` (오케스트레이션 전용)

## 8. 현재 구현 상태
완료:
- MVP1 파이프라인 E2E 실행
- Streamlit 필터/탭/다운로드/금액(천원표시) 반영
- validation/trace 상태전이 엔진 구현

미완료:
- Share 수동 조정/확정 UI
- 업로드 기반 자동 실행 UX (Phase 3)
- overlap ON 정산 운영(Phase 2)

## 9. 단계별 완료 기준
## 9.1 Phase 2 완료 기준 (중첩구간 유도)
1. overlap ON에서 `overlap_group_id` 누락 0건
2. 보전성 위배 0건
3. `share_overlap_audit` 생성 성공
4. integration/regression/e2e 게이트 통과

## 9.2 Phase 3 완료 기준 (Streamlit 자동화 + 확정)
완료 판정은 아래 5개를 모두 충족해야 함.
1. 파일 업로드 자동화
   - 병원/약국/도매 원천 파일 업로드 후 백엔드 파이프라인 자동 실행
2. 자동 검증 및 오류 피드백
   - 인코딩/스키마/필수 컬럼 오류를 UI에서 즉시 안내
3. 수동 조정 및 확정
   - share 값 직접 조정 가능
   - 확정 시 `version`, `status`, `approved_by`, `approved_at` 저장
4. KPI 재반영 일관성
   - 확정 후 KPI 재발행 시 pre/post 집계 일관성 유지
5. 운영 추적성
   - 확정 이력 + trace 상태전이 로그 저장/조회/다운로드 가능

## 9.3 Phase 4 완료 기준 (최종 목표)
1. 사전 수작업 없이 파일 업로드만으로 전체 결과 생성
2. Validation 실패 시 사유 구조화 기록 + 경고 플래그 반영
3. 운영자 관점에서 월/분기/연 정산 업무를 UI만으로 처리 가능

## 10. 비범위 (MVP Guard)
- 경쟁사 점유율/외부 시장데이터 통합
- 환자 레벨 추적
- 도매 간 이동 추적 (Phase 2+)

## 11. 테스트 전략
- `unit`, `contract`, `integration`, `regression`, `e2e`, `smoke`
- Phase 종료 조건:
  - 필수 테스트 100% 통과
  - 필수 실패 0건
  - 필수 산출물 누락 0건

## 12. 리스크 및 대응
1. 원천 컬럼/인코딩 변동
   - 업로드 단계 스키마/인코딩 검사 강화
2. 룰 관리 복잡도 증가
   - 룰 버전/상태/우선순위 관리 고정
3. 정산 신뢰성 이슈
   - 보전성/연장/중첩/재배분 회귀 테스트 상시 운영
