--DROP TABLE IF EXISTS public.review;
CREATE TABLE IF NOT EXISTS public.review
(
    User_id BIGINT NOT NULL,
    Game_id BIGINT NOT NULL,
	Times timestamp NOT NULL,
    Texts text,
    Rating INT NOT NULL CHECK (Rating IN (1, 2, 3, 4, 5)),
    PRIMARY KEY (User_id, Game_id),
    FOREIGN KEY (User_id) REFERENCES public.user(User_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Game_id) REFERENCES public.GAME(Game_id) ON DELETE CASCADE ON UPDATE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.review
    OWNER to postgres;
