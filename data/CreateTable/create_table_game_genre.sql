-- Table: public.game_genre

-- DROP TABLE IF EXISTS public.game_genre;

CREATE TABLE IF NOT EXISTS public.game_genre
(
    game_id bigint NOT NULL,
    genre character varying(30) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT game_genre_pkey PRIMARY KEY (game_id, genre),
    CONSTRAINT game_id_fkey FOREIGN KEY (game_id)
        REFERENCES public.game (game_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game_genre
    OWNER to postgres;