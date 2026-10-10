from app.main import app


def test_schema_names_are_unique():
    """Two response models with one name get mangled names, which breaks the generated
    frontend types (src/api/schema.ts)."""
    names = app.openapi()["components"]["schemas"]
    assert not [n for n in names if "__" in n]
