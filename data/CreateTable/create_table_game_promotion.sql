-- Table: public.game_promotion

-- DROP TABLE IF EXISTS public.game_promotion;

CREATE TABLE IF NOT EXISTS public.game_promotion
(
    game_id bigint NOT NULL,
    promotion_id bigint NOT NULL,
    CONSTRAINT game_promotion_pkey PRIMARY KEY (game_id, promotion_id),
    CONSTRAINT game_id_fkey FOREIGN KEY (game_id)
        REFERENCES public.game (game_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game_promotion
    OWNER to postgres;