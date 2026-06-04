from app.core.schema_compat import ensure_user_identity_columns


if __name__ == "__main__":
    ensure_user_identity_columns()
    print("users identity columns OK")
