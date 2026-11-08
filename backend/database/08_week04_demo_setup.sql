   INSERT INTO class_sections
   (id, course_code, semester_code, lecturer_id, capacity)
VALUES
   (&#39;RACE-01&#39;, &#39;INT2204&#39;, &#39;2026-1&#39;, &#39;GV01&#39;, 1)
ON CONFLICT (id) DO UPDATE
SET capacity = EXCLUDED.capacity;

DELETE FROM enrollments
WHERE class_section_id = &#39;RACE-01&#39;;

DELETE FROM enrollment_events
WHERE class_section_id = &#39;RACE-01&#39;
  AND dataset = &#39;demo&#39;;

SELECT class_id, capacity, enrolled, remaining
FROM v_section_summary
WHERE class_id = &#39;RACE-01&#39;;