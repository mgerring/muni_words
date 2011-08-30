alter table scrape_cc_transcript add column text_vector tsvector;
create trigger text_vector_update before insert or update on scrape_cc_transcript for each row execute procedure tsvector_update_trigger(text_vector, 'pg_catalog.english', text);
create index scrape_cc_transcript_ft on scrape_cc_transcript using gin(text_vector);
