
---

## `docs/04_validation_qa_plan.md`
```md
# Validation & QA Plan — Prescription Data Flow (MVP)

## 1) 목표
정확한 처방 복제가 아니라, **정산 재현성/룰 적용 일관성/분쟁 방지**를 보장한다.

## 2) Validation 체크리스트

### A. 마스터링/매핑
- 약국 UID 미부여 비율
- territory_code 미부여 비율
- territory_source(A/C) 구성비
- 중복 의심 약국:
  - 동일 전화 + 주소 유사
  - 동일 주소 + 약국명 유사

### B. 출고 데이터 품질
- amount_ship 음수/0 이상치
- 분기 경계 누락/급변 탐지
- unknown wholesaler/누락 건수

### C. 룰 적용 품질
- 룰 누락 목록(quarter×territory×brand)
- 전분기 연장 적용 목록 및 근거 룰 버전
- ratio_hosp + ratio_clinic = 1.0 검증

### D. 정산 결과 품질
- Pre 총합 vs Post 총합 보존성
- Pool 합 vs 배분 합 일치(오차 허용)
- 복수 의원 재배분 가중치 합 = 1.0 검증

### E. 미포착 루프
- LOG 생성 규칙 충족 여부
- 상태 전이 유효성(Unverified→Inquired→Confirmed/Rejected)

## 3) 최소 테스트 케이스
- TC1: 룰 없는 구간 → Post=Pre
- TC2: 종병1+의원1 → ratio대로 배분
- TC3: 종병1+의원3 → 의원 몫을 의원 Base 비례로 재배분
- TC4: 룰 누락 + 전분기 룰 존재 → 전분기 연장 적용
- TC5: unknown wholesaler 존재 → LOG 생성 및 Confirmed 시 개선 시뮬레이션

## 4) 산출물
- validation_report (issue_type, severity, entity_id, quarter, details)