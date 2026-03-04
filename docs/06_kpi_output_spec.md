# KPI Output Spec — Prescription Data Flow (MVP)

## 1) rep_kpi_quarter (핵심 결과)
- Grain: `year_quarter × rep_id × territory_code × brand`

### Columns
- year_quarter
- rep_id, rep_name
- territory_code
- brand
- amount_pre_share (BaseAmount)
- amount_post_share
- share_applied_flag
- share_rule_version (nullable)
- share_rule_source (direct/extended/none)
- pool_amount (nullable)
- role_in_rule (hosp/clinic, nullable)
- clinic_realloc_weight (nullable)
- notes (nullable)

## 2) kpi_summary_quarter (요약)
- Grain: `year_quarter`
- Columns:
  - total_pre_share
  - total_post_share
  - share_rules_applied_count
  - extended_rules_count
  - unknown_wholesaler_cases_count

## 3) validation_report (검증 리포트)
- Grain: issue 1 row
- Columns:
  - issue_type (UNMAPPED_PHARMACY, NO_TERRITORY, DUPLICATE_SUSPECT, RULE_MISSING, RULE_EXTENDED, UNKNOWN_WHOLESALER, OUTLIER 등)
  - severity (low/med/high)
  - entity_id (pharmacy_uid or rule_key)
  - year_quarter (nullable)
  - details (string)

## 4) data_quality_flag (옵션)
- `src.validation --emit_data_quality_flag` 실행 시 생성
- Grain: `year_quarter`
- Columns:
  - year_quarter
  - issue_count_total
  - issue_count_high
  - data_quality_flag (`pass`/`fail`)
