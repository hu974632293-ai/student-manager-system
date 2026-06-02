from app.core.database import Base, engine
from app.models import class_teacher_link
from app.models import classes
from app.models import job
from app.models import score
from app.models import student
from app.models import teacher
from app.models import user


def create_all_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    create_all_tables()
