-- Table: public.game_genre

-- DROP TABLE IF EXISTS public.game_genre;

CREATE TABLE IF NOT EXISTS public.promotion
(
    promotion_id bigint PRIMARY KEY,
	start_date date NOT NULL,
	end_date date NOT NULL,
	discount_rate float NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.promotion
    OWNER to postgres;
