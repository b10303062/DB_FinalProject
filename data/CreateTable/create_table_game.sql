-- Table: public.game

-- DROP TABLE IF EXISTS public.game;

CREATE TABLE IF NOT EXISTS public.game
(
    game_id bigint NOT NULL,
    game_name character varying(200) COLLATE pg_catalog."default",
    release_date date,
    price double precision,
    total_achievements integer,
    positive_ratings integer,
    negative_ratings integer,
    CONSTRAINT "GAME_pkey" PRIMARY KEY (game_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game
    OWNER to postgres;