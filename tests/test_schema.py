"""input_schema() filtering, tested against a synthetic fixture (no terraform
binary needed) so this runs in plain CI. Shape mirrors what `terraform
providers schema -json` actually returns — verified against the real
azurerm_storage_account schema at v5.4.0 during development: 102 top-level
attributes, only 28 of them true inputs, the rest computed-only exports.
"""

from modulai.core.schema import input_schema

FIXTURE_RESOURCE_SCHEMA = {
    "version": 3,
    "block": {
        "attributes": {
            "name": {"type": "string", "required": True},
            "account_tier": {"type": "string", "required": True},
            "access_tier": {"type": "string", "optional": True},
            # computed-only — an export, not an input. Must never surface as a variable.
            "primary_blob_endpoint": {"type": "string", "computed": True},
        },
        "block_types": {
            "identity": {
                "nesting_mode": "list",
                "min_items": 0,
                "max_items": 1,
                "block": {
                    "attributes": {
                        "type": {"type": "string", "required": True},
                        "identity_ids": {"type": ["list", "string"], "optional": True},
                        # computed-only, nested — the case that's easy to miss.
                        "principal_id": {"type": "string", "computed": True},
                        "tenant_id": {"type": "string", "computed": True},
                    },
                    "block_types": {},
                },
            }
        },
    },
}


def test_strips_top_level_computed_only():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    assert "primary_blob_endpoint" not in filtered["attributes"]


def test_keeps_top_level_required_and_optional():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    assert set(filtered["attributes"]) == {"name", "account_tier", "access_tier"}


def test_strips_computed_only_inside_nested_block():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    identity_attrs = filtered["block_types"]["identity"]["block"]["attributes"]
    assert "principal_id" not in identity_attrs
    assert "tenant_id" not in identity_attrs
    assert set(identity_attrs) == {"type", "identity_ids"}


def test_preserves_nesting_metadata():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    identity_block_type = filtered["block_types"]["identity"]
    assert identity_block_type["nesting_mode"] == "list"
    assert identity_block_type["max_items"] == 1
