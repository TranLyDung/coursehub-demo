
-- 1. Xóa dữ liệu performance cũ
DELETE FROM enrollment_events
WHERE dataset = 'performance';


-- 2. Sinh 100.000 bản ghi dữ liệu kiểm thử
INSERT INTO enrollment_events (
    student_id,
    class_section_id,
    event_type,
    source,
    dataset,
    occurred_at
)
SELECT
    (ARRAY[
        '22000001',
        '22000002',
        '22000003',
        '22000004'
    ])[1 + (g % 4)::INTEGER],

    (ARRAY[
        'WEB-01',
        'WEB-02',
        'DM-01',
        'PY-01'
    ])[1 + (g % 4)::INTEGER],

    CASE
        WHEN g % 5 = 0 THEN 'CANCELLED'
        ELSE 'CREATED'
    END,

    'generator',
    'performance',

    TIMESTAMP '2025-01-01 00:00:00'
        + (g % 365) * INTERVAL '1 day'
        + (g % 86400) * INTERVAL '1 second'

FROM generate_series(1, 100000) AS g;


-- 3. Cập nhật thống kê bảng
ANALYZE enrollment_events;


-- 4. Kiểm tra số lượng bản ghi theo dataset
SELECT
    dataset,
    COUNT(*) AS row_count
FROM enrollment_events
GROUP BY dataset
ORDER BY dataset;
