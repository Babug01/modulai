"""documented_argument_names()/deprecated_argument_names() parsing, tested
against synthetic doc snippets covering the two real bullet/heading formats
found live: azurerm's plural "Arguments Reference" / "Attributes Reference"
with bare "(Optional)", and AWS's singular "Argument Reference" /
"Attribute Reference" with compound qualifiers like "(Optional, Forces new
resource)" and "(Optional, **Deprecated**)".
"""

from modulai.core.docs import deprecated_argument_names, documented_argument_names

AZURERM_STYLE_DOC = """
## Arguments Reference

The following arguments are supported:

* `name` - (Required) Specifies the name of the storage account.

* `access_tier` - (Optional) Defines the access tier. Defaults to `Hot`.

---

A `network_rules` block supports the following:

* `default_action` - (Required) Specifies the default action.

## Attributes Reference

In addition to the Arguments listed above - the following Attributes are exported:

* `id` - The ID of the Storage Account.

* `primary_blob_endpoint` - The endpoint URL for blob storage.
"""

AWS_STYLE_DOC = """
## Argument Reference

This resource supports the following arguments:

* `bucket` - (Optional, Forces new resource) Name of the bucket.

* `acl` - (Optional, **Deprecated**) Canned ACL to apply.

## Attribute Reference

This resource exports the following attributes in addition to the arguments above:

* `arn` - ARN of the bucket.

* `tags_all` - A map of tags assigned to the resource, including those inherited from the provider default_tags configuration block.
"""


def test_azurerm_style_bare_optional_required():
    names = documented_argument_names(AZURERM_STYLE_DOC)
    assert {"name", "access_tier", "default_action"} <= names


def test_azurerm_style_excludes_attributes_section():
    names = documented_argument_names(AZURERM_STYLE_DOC)
    assert "id" not in names
    assert "primary_blob_endpoint" not in names


def test_aws_style_compound_qualifiers():
    names = documented_argument_names(AWS_STYLE_DOC)
    assert {"bucket", "acl"} <= names


def test_aws_style_singular_heading_excludes_attributes_section():
    names = documented_argument_names(AWS_STYLE_DOC)
    assert "arn" not in names
    assert "tags_all" not in names


def test_deprecated_argument_is_flagged():
    # acl is "(Optional, **Deprecated**)" in the fixture above.
    assert deprecated_argument_names(AWS_STYLE_DOC) == {"acl"}


def test_non_deprecated_argument_is_not_flagged():
    # bucket is "(Optional, Forces new resource)" — no Deprecated marker.
    assert "bucket" not in deprecated_argument_names(AWS_STYLE_DOC)


def test_azurerm_style_doc_with_no_deprecated_args_returns_empty_set():
    assert deprecated_argument_names(AZURERM_STYLE_DOC) == set()


# Mirrors the real aws_s3_bucket collision: `object_lock_enabled` is a genuine,
# current top-level argument, but a *different*, nested block's doc section
# happens to have its own argument with the exact same name, marked Deprecated.
AMBIGUOUS_NAME_DOC = """
## Argument Reference

This resource supports the following arguments:

* `object_lock_enabled` - (Optional) Whether this bucket has an Object Lock configuration enabled.
* `object_lock_configuration` - (Optional, **Deprecated**) Configuration of object locking.

### `object_lock_configuration` Block

The `object_lock_configuration` configuration block supports the following arguments:

* `object_lock_enabled` - (Optional, **Deprecated**) Whether this bucket has an Object Lock configuration enabled. Use the top-level argument instead.
"""


def test_name_deprecated_in_one_scope_but_not_another_is_not_flagged():
    # object_lock_enabled has one non-deprecated bullet and one deprecated
    # bullet — ambiguous, so it must NOT be treated as globally deprecated.
    assert "object_lock_enabled" not in deprecated_argument_names(AMBIGUOUS_NAME_DOC)


def test_name_deprecated_in_every_occurrence_is_still_flagged():
    # object_lock_configuration only ever appears with the Deprecated marker.
    assert "object_lock_configuration" in deprecated_argument_names(AMBIGUOUS_NAME_DOC)
