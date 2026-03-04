"""Column label mapping for bilingual (en + ko) headers."""

from __future__ import annotations

import pandas as pd


COLUMN_LABEL_KO: dict[str, str] = {
    "ship_id": "출고ID",
    "ship_date": "출고일",
    "year_month": "연월",
    "year_quarter": "연분기",
    "year": "연도",
    "amount_ship": "출고금액",
    "amount_supply": "공급금액",
    "amount_pre_share": "쉐어전금액",
    "amount_post_share": "쉐어후금액",
    "qty": "수량",
    "brand": "브랜드",
    "sku": "SKU",
    "territory_code": "영업권역코드",
    "territory_source": "권역소스",
    "pharmacy_uid": "약국UID",
    "pharmacy_key": "약국매칭키",
    "pharmacy_name": "약국명",
    "pharmacy_addr": "약국주소",
    "pharmacy_tel": "약국전화",
    "pharmacy_account_id": "약국거래처ID",
    "pharmacy_provider_id": "약국요양기호",
    "pharmacy_type_code": "약국종별코드",
    "pharmacy_type_name": "약국종별명",
    "pharmacy_coord_x": "약국좌표X",
    "pharmacy_coord_y": "약국좌표Y",
    "pharmacy_opened_date": "약국개설일",
    "provider_id": "요양기호",
    "provider_name": "요양기관명",
    "provider_type_code": "종별코드",
    "provider_type_name": "종별명",
    "provider_addr": "요양기관주소",
    "provider_tel": "요양기관전화",
    "coord_x": "좌표X",
    "coord_y": "좌표Y",
    "opened_date": "개설일",
    "wholesaler_id": "도매상ID",
    "wholesaler_name": "도매상명",
    "wholesaler_raw_name": "도매원본명",
    "wholesaler_addr_road": "도매도로명주소",
    "wholesaler_addr_jibun": "도매지번주소",
    "wholesaler_tel": "도매전화",
    "biz_type": "업종명",
    "business_status": "영업상태",
    "lat": "위도",
    "lon": "경도",
    "as_of_date": "기준일자",
    "provider_org_code": "제공기관코드",
    "provider_org_name": "제공기관명",
    "active_flag": "활성여부",
    "is_valid_wholesaler": "유효도매여부",
    "mapping_quality_flag": "매핑품질플래그",
    "data_source": "데이터소스",
    "source_file": "원천파일",
    "source_sheet": "원천시트",
    "source_row_id": "원천행ID",
    "branch_id": "지점ID",
    "branch_name": "지점명",
    "region_group": "권역그룹",
    "rep_id": "담당자ID",
    "rep_name": "담당자명",
    "rep_role": "담당유형",
    "hire_date": "입사일",
    "grade": "직급",
    "valid_from": "유효시작일",
    "valid_to": "유효종료일",
    "assign_source": "배정소스",
    "rule_name": "검증룰명",
    "metric_value": "지표값",
    "threshold": "허용기준",
    "status": "상태",
    "note": "비고",
}


def bilingual_column_name(col: str) -> str:
    ko = COLUMN_LABEL_KO.get(col)
    return f"{col} ({ko})" if ko else col


def to_bilingual_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: bilingual_column_name(c) for c in df.columns})
