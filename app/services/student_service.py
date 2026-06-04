from typing import Optional

from sqlalchemy.orm import Session

from app.core.response import fail, success
from app.dao import students as student_dao
from app.services.access_scope_service import AccessScopeService
from app.views.schemas.student import StudentCommentRequest, StudentCreate


SUPPORTED_COMMENT_STYLES = {"正式", "鼓励", "简洁", "详细", "班主任口吻"}


class StudentService:
    @staticmethod
    def _scope_kwargs(db: Session, current_user=None) -> dict:
        if current_user is None or AccessScopeService.is_admin(current_user):
            return {}
        return {"student_ids": AccessScopeService.allowed_student_ids(db, current_user)}

    @staticmethod
    def _format_student_profile(student) -> str:
        parts = []
        if student.gender:
            parts.append(f"性别{student.gender}")
        if student.age is not None:
            parts.append(f"年龄{student.age}岁")
        if student.native_place:
            parts.append(f"籍贯{student.native_place}")
        if student.education:
            parts.append(f"学历{student.education}")
        if student.major:
            parts.append(f"专业为{student.major}")
        if student.graduate_school:
            parts.append(f"毕业于{student.graduate_school}")
        if student.enrollment_date:
            parts.append(f"入学时间为{student.enrollment_date}")
        if student.graduation_date:
            parts.append(f"毕业时间为{student.graduation_date}")
        if not parts:
            return "基础信息暂不完整"
        return "，".join(parts)

    @staticmethod
    def _build_comment(student, style: str, extra_notes: Optional[str]) -> str:
        profile = StudentService._format_student_profile(student)
        notes = extra_notes.strip() if extra_notes else ""
        notes_sentence = f"近期表现方面，{notes}。" if notes else ""

        templates = {
            "正式": (
                f"{student.name}同学，{profile}。该生整体表现稳定，能够遵守学校纪律，"
                f"学习态度端正，与同学相处融洽。{notes_sentence}希望今后继续保持良好习惯，"
                "进一步提升综合能力。"
            ),
            "鼓励": (
                f"{student.name}同学一直在努力成长，{profile}。你具备继续进步的潜力，"
                f"只要保持专注和自信，就能在学习和综合表现上取得更好的成绩。{notes_sentence}"
                "期待你不断突破自己。"
            ),
            "简洁": (
                f"{student.name}同学表现良好，{profile}。{notes_sentence}"
                "望继续保持优点，改进不足。"
            ),
            "详细": (
                f"{student.name}同学，{profile}。从综合表现看，该生能够较好适应学习生活，"
                f"具备一定的自我管理意识和发展潜力。{notes_sentence}建议后续在专业学习、"
                "沟通表达和实践能力方面继续加强，形成更加稳定的学习节奏和成长目标。"
            ),
            "班主任口吻": (
                f"{student.name}同学，老师看到你在学习和生活中的努力，{profile}。"
                f"{notes_sentence}希望你继续踏实认真，遇到问题及时沟通，"
                "把已有的优点坚持下去，也把薄弱的地方一点点补起来。"
            ),
        }
        return templates[style]

    @staticmethod
    def list_students(db: Session, skip: int = 0, limit: int = 10, current_user=None):
        students, total = student_dao.get_allstudents(
            db,
            skip=skip,
            limit=limit,
            **StudentService._scope_kwargs(db, current_user),
        )
        return success({"total": total, "students": students}, "students found")

    @staticmethod
    def get_student(db: Session, student_id=None, student_name=None, class_id=None, current_user=None):
        select_id, select_name, select_class = student_dao.get_student(
            db,
            student_id=student_id,
            student_name=student_name,
            class_id=class_id,
            **StudentService._scope_kwargs(db, current_user),
        )
        return success(
            {
                "select_id": select_id,
                "select_name": select_name,
                "class_id": select_class,
            },
            "student found",
        )

    @staticmethod
    def create_student(db: Session, student: StudentCreate):
        data = student.model_dump()
        data["is_deleted"] = False
        if data.get("consultant_id") in (0, None):
            data.pop("consultant_id", None)
        try:
            return success(student_dao.create_student(db, data), "student created")
        except ValueError as exc:
            return fail(str(exc))

    @staticmethod
    def update_student(db: Session, student_id: str, student: StudentCreate, current_user=None):
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")
        update_data = student.model_dump(exclude_unset=True)
        update_data.pop("student_id", None)
        update_data.pop("is_deleted", None)
        updated = student_dao.update_student(db, student_id, update_data)
        if not updated:
            return fail("student not found")
        return success(updated, "student updated")

    @staticmethod
    def delete_student(db: Session, student_id: int = None, student_name: str = None, current_user=None):
        if current_user is not None and student_id and not AccessScopeService.can_access_student(db, current_user, str(student_id)):
            return fail("permission denied")
        deleted = student_dao.delete_student(db, student_id, student_name)
        if not deleted:
            return fail("student not found")
        return success(deleted, "student deleted")

    @staticmethod
    def generate_comment(db: Session, request: StudentCommentRequest, current_user=None):
        style = (request.style or "正式").strip()
        if style not in SUPPORTED_COMMENT_STYLES:
            return fail("unsupported comment style")

        student_id = request.student_id.strip()
        if not student_id:
            return fail("student_id is required")
        if current_user is not None and not AccessScopeService.can_access_student(db, current_user, student_id):
            return fail("permission denied")

        student = student_dao.get_student_by_student_id(db, student_id)
        if not student:
            return fail("student not found")

        comment = StudentService._build_comment(student, style, request.extra_notes)
        return success(
            {
                "student_id": student.student_id,
                "name": student.name,
                "style": style,
                "comment": comment,
            },
            "comment generated",
        )
