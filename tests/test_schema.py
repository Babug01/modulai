"""input_schema() filtering, tested against a synthetic fixture (no terraform
binary needed) so this runs in plain CI. Shape mirrors what `terraform
providers schema -json` actually returns — verified against the real
azurerm_storage_account schema at v5.4.0 during development: 102 top-level
attributes, only 28 of them true inputs, the rest computed-only exports.
"""

from modulai.core.schema import ALERT_RESOURCE_TYPE_BY_PROVIDER, cross_reference_with_docs, exclude_deprecated, input_schema


def test_alert_resource_type_is_cloud_specific_not_hardcoded_to_azure():
    # Found live: an earlier version of generate.py hardcoded
    # azurerm_monitor_metric_alert regardless of target cloud. Each provider
    # must map to its own real alert resource type, and they must differ —
    # a passing test here doesn't guarantee the *names* are correct (that's
    # what the live schema-fetch check covers), only that the mapping isn't
    # collapsed back to one Azure-specific value for every provider.
    assert ALERT_RESOURCE_TYPE_BY_PROVIDER["azurerm"] == "azurerm_monitor_metric_alert"
    assert ALERT_RESOURCE_TYPE_BY_PROVIDER["aws"] == "aws_cloudwatch_metric_alarm"
    assert ALERT_RESOURCE_TYPE_BY_PROVIDER["google"] == "google_monitoring_alert_policy"
    assert len(set(ALERT_RESOURCE_TYPE_BY_PROVIDER.values())) == len(ALERT_RESOURCE_TYPE_BY_PROVIDER)

FIXTURE_RESOURCE_SCHEMA = {
    "version": 3,
    "block": {
        "attributes": {
            "name": {"type": "string", "required": True},
            "account_tier": {"type": "string", "required": True},
            "access_tier": {"type": "string", "optional": True},
            # computed-only — an export, not an input. Must never surface as a variable.
            "primary_blob_endpoint": {"type": "string", "computed": True},
            # `id` marked optional+computed — seen live on azurerm_key_vault @ v5.4.0.
            # Must be dropped anyway: it's every resource's implicit identifier.
            "id": {"type": "string", "optional": True, "computed": True},
            # A genuine optional+computed *input* (e.g. access_policy-shaped) —
            # proves the id-exclusion is name-specific, not "drop anything computed".
            "access_policy": {"type": ["list", "object"], "optional": True, "computed": True},
            # Same optional+computed shape as `id`, but provider-specific — seen
            # live as AWS's `tags_all`. Not caught by the id-exclusion; only
            # cross_reference_with_docs (below) catches this class of case.
            "tags_all": {"type": ["map", "string"], "optional": True, "computed": True},
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
    assert set(filtered["attributes"]) == {"name", "account_tier", "access_tier", "access_policy", "tags_all"}


def test_drops_top_level_id_even_when_optional_and_computed():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    assert "id" not in filtered["attributes"]


def test_keeps_other_optional_and_computed_attributes():
    """id is special-cased by name — optional+computed alone must not be
    treated as a signal to drop something; access_policy is exactly that
    combination on the real azurerm_key_vault schema and is a real input."""
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    assert "access_policy" in filtered["attributes"]


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


# documented_names below mirrors what documented_argument_names() would
# extract from a real doc: every real input's name, deliberately missing
# `tags_all` — it's never documented as settable, exactly like the real AWS case.
DOCUMENTED_NAMES = {"name", "account_tier", "access_tier", "access_policy", "type", "identity_ids"}


def test_cross_reference_drops_undocumented_optional_computed_attribute():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    cross_referenced = cross_reference_with_docs(filtered, DOCUMENTED_NAMES)
    assert "tags_all" not in cross_referenced["attributes"]


def test_cross_reference_keeps_documented_attributes():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    cross_referenced = cross_reference_with_docs(filtered, DOCUMENTED_NAMES)
    assert set(cross_referenced["attributes"]) == {"name", "account_tier", "access_tier", "access_policy"}


def test_cross_reference_applies_inside_nested_blocks():
    filtered = input_schema(FIXTURE_RESOURCE_SCHEMA)
    cross_referenced = cross_reference_with_docs(filtered, DOCUMENTED_NAMES)
    identity_attrs = cross_referenced["block_types"]["identity"]["block"]["attributes"]
    assert set(identity_attrs) == {"type", "identity_ids"}


# Mirrors the real aws_s3_bucket shape: a deprecated top-level scalar (acl)
# alongside a deprecated whole nested block (versioning) that still has its
# own non-deprecated-looking inner attributes — proving exclude_deprecated
# drops the block wholesale instead of recursing into it and keeping those.
DEPRECATED_FIXTURE = {
    "attributes": {
        "bucket": {"type": "string", "optional": True},
        "acl": {"type": "string", "optional": True},
    },
    "block_types": {
        "versioning": {
            "nesting_mode": "list",
            "min_items": 0,
            "max_items": 1,
            "block": {
                "attributes": {"enabled": {"type": "bool", "optional": True}},
                "block_types": {},
            },
        },
        "logging": {
            "nesting_mode": "list",
            "min_items": 0,
            "max_items": 1,
            "block": {
                "attributes": {"target_bucket": {"type": "string", "required": True}},
                "block_types": {},
            },
        },
    },
}

DEPRECATED_NAMES = {"acl", "versioning"}


def test_exclude_deprecated_drops_top_level_attribute():
    result = exclude_deprecated(DEPRECATED_FIXTURE, DEPRECATED_NAMES)
    assert "acl" not in result["attributes"]
    assert "bucket" in result["attributes"]


def test_exclude_deprecated_drops_whole_nested_block_without_recursing():
    result = exclude_deprecated(DEPRECATED_FIXTURE, DEPRECATED_NAMES)
    assert "versioning" not in result["block_types"]


def test_exclude_deprecated_keeps_non_deprecated_block():
    result = exclude_deprecated(DEPRECATED_FIXTURE, DEPRECATED_NAMES)
    assert "logging" in result["block_types"]
    assert set(result["block_types"]["logging"]["block"]["attributes"]) == {"target_bucket"}


def test_exclude_deprecated_with_empty_set_is_a_no_op():
    result = exclude_deprecated(DEPRECATED_FIXTURE, set())
    assert set(result["attributes"]) == {"bucket", "acl"}
    assert set(result["block_types"]) == {"versioning", "logging"}
