import pytest

from src.product_catalog import get_brand_catalog


@pytest.mark.unit
def test_product_catalog_has_20_brands_and_sku_prices():
    catalog = get_brand_catalog()
    assert len(catalog) == 20

    for brand_item in catalog:
        assert isinstance(brand_item["brand"], str) and brand_item["brand"]
        assert len(brand_item["sku_options"]) >= 1
        for sku_item in brand_item["sku_options"]:
            assert isinstance(sku_item["sku"], str) and sku_item["sku"]
            assert isinstance(sku_item["pack_size"], str) and sku_item["pack_size"]
            assert int(sku_item["pack_units"]) > 0
            assert float(sku_item["price_per_unit"]) > 0
            assert float(sku_item["price_per_pack"]) > 0
