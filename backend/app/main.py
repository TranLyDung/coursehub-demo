from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import engine
from .schemas import EnrollmentCreate


logger = logging.getLogger(__name__)

app = FastAPI(
    title="CourseHub API",
    version="0.4.0",
    description="API quan ly hoc phan va dang ky hoc phan",
)


# =========================================================
# 1. ROOT AND HEALTH CHECK
# =========================================================

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CourseHub API dang hoat dong"}


@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    except SQLAlchemyError as exc:
        logger.exception("Khong ket noi duoc co so du lieu")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong ket noi duoc co so du lieu",
        ) from exc

    return {
        "status": "ok",
        "database": "connected",
    }


# =========================================================
# 2. COURSES
# =========================================================

@app.get("/courses")
def list_courses(
    q: str | None = Query(default=None, min_length=1),
) -> list[dict[str, object]]:
    sql = """
        SELECT code, name, credits
        FROM courses
    """

    parameters: dict[str, object] = {}

    if q is not None:
        keyword = q.strip().lower()

        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu khoa tim kiem khong duoc rong",
            )

        sql += """
            WHERE LOWER(code) LIKE :keyword
               OR LOWER(name) LIKE :keyword
        """
        parameters["keyword"] = f"%{keyword}%"

    sql += " ORDER BY code"

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql),
            parameters,
        ).mappings().all()

    return [dict(row) for row in rows]


@app.get("/courses/{course_code}")
def get_course(course_code: str) -> dict[str, object]:
    sql = """
        SELECT code, name, credits
        FROM courses
        WHERE code = :course_code
    """

    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"course_code": course_code.upper()},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay hoc phan",
        )

    return dict(row)


# =========================================================
# 3. CLASS SECTIONS
# =========================================================

@app.get("/sections")
def list_sections(
    available_only: bool = False,
) -> list[dict[str, object]]:
    sql = """
        SELECT class_id, course_code, capacity, enrolled, remaining
        FROM v_section_summary
    """

    if available_only:
        sql += " WHERE remaining > 0"

    sql += " ORDER BY class_id"

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql)
        ).mappings().all()

    return [dict(row) for row in rows]


# =========================================================
# 4. ENROLLMENTS - LIST ALL
# =========================================================

@app.get("/enrollments")
def list_enrollments() -> list[dict[str, object]]:
    sql = """
        SELECT
            e.student_id,
            s.name AS student_name,
            e.class_section_id,
            c.code AS course_code,
            c.name AS course_name,
            e.registered_at
        FROM enrollments AS e
        JOIN students AS s
            ON s.id = e.student_id
        JOIN class_sections AS cs
            ON cs.id = e.class_section_id
        JOIN courses AS c
            ON c.code = cs.course_code
        ORDER BY e.student_id, e.class_section_id
    """

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql)
        ).mappings().all()

    return [dict(row) for row in rows]


# =========================================================
# 5. ENROLLMENTS - LIST BY STUDENT
# =========================================================

@app.get("/students/{student_id}/enrollments")
def list_student_enrollments(
    student_id: str,
) -> list[dict[str, object]]:
    student_sql = """
        SELECT id
        FROM students
        WHERE id = :student_id
    """

    enrollment_sql = """
        SELECT
            e.student_id,
            s.name AS student_name,
            cs.id AS class_section_id,
            c.code AS course_code,
            c.name AS course_name,
            e.registered_at
        FROM enrollments AS e
        JOIN students AS s
            ON s.id = e.student_id
        JOIN class_sections AS cs
            ON cs.id = e.class_section_id
        JOIN courses AS c
            ON c.code = cs.course_code
        WHERE e.student_id = :student_id
        ORDER BY cs.id
    """

    with engine.connect() as connection:
        student = connection.execute(
            text(student_sql),
            {"student_id": student_id},
        ).first()

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )

        rows = connection.execute(
            text(enrollment_sql),
            {"student_id": student_id},
        ).mappings().all()

    return [dict(row) for row in rows]


# =========================================================
# 6. ENROLLMENTS - CREATE
# =========================================================

@app.post(
    "/enrollments",
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    payload: EnrollmentCreate,
) -> dict[str, object]:

    student_sql = """
        SELECT id
        FROM students
        WHERE id = :student_id
    """

    # Lock the class-section row to help prevent concurrent
    # registrations from exceeding the class capacity.
    section_sql = """
        SELECT id, capacity
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    count_sql = """
        SELECT COUNT(*)
        FROM enrollments
        WHERE class_section_id = :class_section_id
    """

    duplicate_sql = """
        SELECT 1
        FROM enrollments
        WHERE student_id = :student_id
          AND class_section_id = :class_section_id
    """

    insert_sql = """
        INSERT INTO enrollments (
            student_id,
            class_section_id
        )
        VALUES (
            :student_id,
            :class_section_id
        )
    """

    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    # All validation and insertion happen in one transaction.
    with engine.begin() as connection:

        student = connection.execute(
            text(student_sql),
            {"student_id": payload.student_id},
        ).first()

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )

        section = connection.execute(
            text(section_sql),
            {
                "class_section_id": payload.class_section_id,
            },
        ).mappings().first()

        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan",
            )

        duplicated = connection.execute(
            text(duplicate_sql),
            parameters,
        ).first()

        if duplicated is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sinh vien da dang ky lop nay",
            )

        enrolled = connection.execute(
            text(count_sql),
            {
                "class_section_id": payload.class_section_id,
            },
        ).scalar_one()

        if int(enrolled) >= int(section["capacity"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lop hoc phan da het cho",
            )

        connection.execute(
            text(insert_sql),
            parameters,
        )

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }


# =========================================================
# 7. ENROLLMENTS - DELETE
# =========================================================

@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    student_id: str,
    class_section_id: str,
) -> Response:
    sql = """
        DELETE FROM enrollments AS e
        USING class_sections AS cs
        WHERE e.class_section_id = cs.id
          AND e.student_id = :student_id
          AND cs.class_id = :class_section_id
    """

    with engine.begin() as connection:
        result = connection.execute(
            text(sql),
            {
                "student_id": student_id,
                "class_section_id": class_section_id,
            },
        )

        deleted = result.rowcount

    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay dang ky can huy",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
