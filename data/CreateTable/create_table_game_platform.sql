-- Table: public.game_platform

-- DROP TABLE IF EXISTS public.game_platform;

CREATE TABLE IF NOT EXISTS public.game_platform
(
    game_id bigint NOT NULL,
    platform character varying(20) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT game_platform_pkey PRIMARY KEY (game_id, platform),
    CONSTRAINT game_id_fkey FOREIGN KEY (game_id)
        REFERENCES public.game (game_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game_platform
    OWNER to postgres;