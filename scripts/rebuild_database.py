from pathlib import Path
import os
import sys

from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TABLES = [
    "users",
    "class_teacher_link",
    "student_scores",
    "student_jobs",
    "students",
    "teachers",
    "classes",
]


def load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()


def main() -> None:
    load_env()

    from app.core.database import Base
    from app.models.class_teacher_link import class_teacher_link  # noqa: F401
    from app.models.classes import Class  # noqa: F401
    from app.models.job import StudentJob  # noqa: F401
    from app.models.score import StudentScore  # noqa: F401
    from app.models.student import Student  # noqa: F401
    from app.models.teacher import Teacher  # noqa: F401
    from app.models.user import User  # noqa: F401

    url = (
        f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
        "?charset=utf8mb4"
    )
    engine = create_engine(url, pool_pre_ping=True)

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            print(f"dropped {table}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    Base.metadata.create_all(bind=engine)
    print("created tables")

    inspector = inspect(engine)
    for table in sorted(inspector.get_table_names()):
        if table in TABLES:
            print(f"[{table}]")
            for column in inspector.get_columns(table):
                nullable = "NULL" if column.get("nullable") else "NOT NULL"
                print(f"  {column['name']} {column['type']} {nullable}")


if __name__ == "__main__":
    main()
