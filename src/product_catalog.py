"""Product catalog SSOT for synthetic shipment generation."""

from __future__ import annotations

from collections import defaultdict


def _v(
    brand: str,
    formulation: str,
    strength: str,
    pack_size: str,
    pack_units: int,
    price_per_unit: float,
    *,
    sku_label: str | None = None,
) -> dict[str, object]:
    unit = float(price_per_unit)
    units = int(pack_units)
    return {
        "brand": brand,
        "formulation": formulation,
        "strength": strength,
        "pack_size": pack_size,
        "pack_units": units,
        "price_per_unit": unit,
        "pack_price": float(round(unit * units, 0)),
        "sku_label": sku_label,
    }


PRODUCT_VARIANTS: list[dict[str, object]] = [
    _v("록소르정", "정", "5mg", "30정", 30, 126.67),
    _v("록소르정", "정", "10mg", "300정", 300, 110.00),
    _v("자누비아정", "정", "300mg", "30정", 30, 1400.00),
    _v("자누비아정", "정", "600mg", "300정", 300, 1300.00),
    _v("자누비아정", "정", "1000mg", "30정", 30, 2533.33),
    _v("아모잘탄정", "정", "5/50mg", "30정", 30, 483.33),
    _v("아모잘탄정", "정", "5/100mg", "300정", 300, 453.33),
    _v("아모잘탄정", "정", "10/50mg", "30정", 30, 570.00),
    _v("리피토정", "정", "10mg", "30정", 30, 330.00),
    _v("리피토정", "정", "20mg", "300정", 300, 306.67),
    _v("리피토정", "정", "40mg", "30정", 30, 450.00),
    _v("플라빅스정", "정", "75mg", "300정", 300, 420.00),
    _v("트라젠타정", "정", "5mg", "30정", 30, 626.67),
    _v("네시나정", "정", "12.5mg", "30정", 30, 576.67),
    _v("네시나정", "정", "25mg", "300정", 300, 536.67),
    _v("가브스정", "정", "50mg", "30정", 30, 496.67),
    _v("가브스정", "정", "50/500mg", "30정", 30, 670.00, sku_label="가브스메트정 50/500mg"),
    _v("가브스정", "정", "50/850mg", "300정", 300, 626.67, sku_label="가브스메트정 50/850mg"),
    _v("글루코파지정", "정", "500mg", "300정", 300, 123.33),
    _v("글루코파지정", "정", "750mg", "30정", 30, 156.67),
    _v("글루코파지정", "정", "1000mg", "300정", 300, 173.33),
    _v("로수젯정", "정", "10/5mg", "30정", 30, 670.00),
    _v("로수젯정", "정", "10/10mg", "300정", 300, 636.67),
    _v("아토젯정", "정", "10/10mg", "30정", 30, 630.00),
    _v("아토젯정", "정", "10/20mg", "300정", 300, 596.67),
    _v("엑스포지정", "정", "5/80mg", "30정", 30, 540.00),
    _v("엑스포지정", "정", "5/160mg", "300정", 300, 503.33),
    _v("엑스포지정", "정", "10/160mg", "30정", 30, 646.67),
    _v("카나브정", "정", "30mg", "30정", 30, 330.00),
    _v("카나브정", "정", "60mg", "300정", 300, 303.33),
    _v("카나브정", "정", "120mg", "30정", 30, 470.00),
    _v("올메텍정", "정", "10mg", "30정", 30, 303.33),
    _v("올메텍정", "정", "20mg", "300정", 300, 276.67),
    _v("올메텍정", "정", "40mg", "30정", 30, 396.67),
    _v("디아미크롱서방정", "서방정", "30mg", "30정", 30, 206.67),
    _v("디아미크롱서방정", "서방정", "60mg", "300정", 300, 190.00),
    _v("아토르바정", "정", "10mg", "30정", 30, 273.33),
    _v("아토르바정", "정", "20mg", "300정", 300, 253.33),
    _v("아토르바정", "정", "40mg", "30정", 30, 386.67),
    _v("타미플루캡슐", "캡슐", "30mg", "30C", 30, 536.67),
    _v("타미플루캡슐", "캡슐", "45mg", "500C", 500, 472.00),
    _v("타미플루캡슐", "캡슐", "75mg", "30C", 30, 713.33),
    _v("세파클러캡슐", "캡슐", "250mg", "30C", 30, 243.33),
    _v("세파클러캡슐", "캡슐", "500mg", "500C", 500, 194.00),
    _v("서스펜정", "정", "100mg", "30정", 30, 230.00),
    _v("서스펜정", "정", "200mg", "300정", 300, 213.33),
    _v("넥시움정", "정", "20mg", "30정", 30, 363.33),
    _v("넥시움정", "정", "40mg", "300정", 300, 336.67),
]

COMPANY_NAME = "제약사A"


def get_brand_catalog() -> list[dict[str, object]]:
    """Return brand-level catalog with variant metadata and prices."""
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in PRODUCT_VARIANTS:
        sku = str(item.get("sku_label") or f"{item['brand']} {item['strength']}")
        grouped[str(item["brand"])].append(
            {
                "sku": sku,
                "manufacturer_name": COMPANY_NAME,
                "formulation": str(item["formulation"]),
                "strength": str(item["strength"]),
                "pack_size": str(item["pack_size"]),
                "pack_units": int(item["pack_units"]),
                "price_per_unit": float(item["price_per_unit"]),
                "price_per_pack": float(item["pack_price"]),
            }
        )

    return [{"brand": brand, "sku_options": options} for brand, options in grouped.items()]
