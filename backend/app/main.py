@app.post(
    "/enrollments",
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(payload: EnrollmentCreate) -> dict[str, str]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"

    lock_section_sql = """
        SELECT id, capacity
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    duplicate_sql = """
        SELECT 1
        FROM enrollments
        WHERE student_id = :student_id
        AND class_section_id = :class_section_id
    """

    count_sql = """
        SELECT COUNT(*)
        FROM enrollments
        WHERE class_section_id = :class_section_id
    """

    insert_sql = """
        INSERT INTO enrollments (student_id, class_section_id)
        VALUES (:student_id, :class_section_id)
    """

    event_sql = """
        INSERT INTO enrollment_events
        (student_id, class_section_id, event_type, source, dataset)
        VALUES
        (:student_id, :class_section_id, 'CREATED', 'api', 'demo')
    """

    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    try:
        with engine.begin() as connection:
            # Kiểm tra sinh viên có tồn tại không
            student = connection.execute(
                text(student_sql),
                {"student_id": payload.student_id},
            ).first()

            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay sinh vien",
                )

            # Khóa lớp học phần để tránh đăng ký vượt quá sức chứa
            section = connection.execute(
                text(lock_section_sql),
                {"class_section_id": payload.class_section_id},
            ).mappings().first()

            if section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay lop hoc phan",
                )

            # Kiểm tra đăng ký trùng
            duplicated = connection.execute(
                text(duplicate_sql),
                parameters,
            ).first()

            if duplicated is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Sinh vien da dang ky lop nay",
                )

            # Đếm số sinh viên đã đăng ký
            enrolled = connection.execute(
                text(count_sql),
                {
                    "class_section_id": payload.class_section_id
                },
            ).scalar_one()

            if int(enrolled) >= int(section["capacity"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Lop hoc phan da het cho",
                )

            # Thêm đăng ký mới
            connection.execute(
                text(insert_sql),
                parameters,
            )

            # Ghi nhận sự kiện đăng ký
            connection.execute(
                text(event_sql),
                parameters,
            )

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dang ky xung dot voi du lieu hien tai",
        ) from exc

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }


@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    student_id: str,
    class_section_id: str,
) -> Response:

    lock_section_sql = """
        SELECT id
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    delete_sql = """
        DELETE FROM enrollments
        WHERE student_id = :student_id
        AND class_section_id = :class_section_id
        RETURNING student_id
    """

    event_sql = """
        INSERT INTO enrollment_events
        (student_id, class_section_id, event_type, source, dataset)
        VALUES
        (:student_id, :class_section_id, 'CANCELLED', 'api', 'demo')
    """

    parameters = {
        "student_id": student_id,
        "class_section_id": class_section_id,
    }

    with engine.begin() as connection:

        # Khóa lớp học phần
        section = connection.execute(
            text(lock_section_sql),
            {"class_section_id": class_section_id},
        ).first()

        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan",
            )

        # Xóa đăng ký học phần
        deleted = connection.execute(
            text(delete_sql),
            parameters,
        ).first()

        if deleted is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay dang ky can huy",
            )

        # Ghi nhận sự kiện hủy đăng ký
        connection.execute(
            text(event_sql),
            parameters,
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )




