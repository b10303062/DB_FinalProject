-- Table: public.game_publisher

-- DROP TABLE IF EXISTS public.game_publisher;

CREATE TABLE IF NOT EXISTS public.game_publisher
(
    game_id bigint NOT NULL,
    publisher character varying(100) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT game_publisher_pkey PRIMARY KEY (game_id, publisher),
    CONSTRAINT game_id_fkey FOREIGN KEY (game_id)
        REFERENCES public.game (game_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game_publisher
    OWNER to postgres;