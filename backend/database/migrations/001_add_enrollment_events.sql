   BEGIN;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) NOT NULL PRIMARY KEY,
    description VARCHAR(200) NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
   );

CREATE TABLE enrollment_events (
   id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
   student_id VARCHAR(8) NOT NULL REFERENCES students(id),
   class_section_id VARCHAR(20) NOT NULL REFERENCES class_sections(id),
   event_type VARCHAR(20) NOT NULL,
   source VARCHAR(20) NOT NULL DEFAULT &#39;api&#39;,
   dataset VARCHAR(20) NOT NULL DEFAULT &#39;demo&#39;,
   occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  
   CONSTRAINT ck_enrollment_events_type
   CHECK (event_type IN (&#39;CREATED&#39;, &#39;CANCELLED&#39;)),
   CONSTRAINT ck_enrollment_events_dataset
   CHECK (dataset IN (&#39;demo&#39;, &#39;performance&#39;))
   );

INSERT INTO schema_migrations (version, description)
VALUES (&#39;001&#39;, &#39;Add enrollment event audit table&#39;);

COMMIT;