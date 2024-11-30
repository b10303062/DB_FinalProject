--DROP TABLE IF EXISTS public.game_status;

CREATE TABLE IF NOT EXISTS public.game_status
(
    user_id bigint NOT NULL,
	game_id bigint NOT NULL,
	playtime bigint NOT NULL,
	acheivements int NOT NULL,
	status varchar(10) NOT NULL CHECK (status IN ('Buyed', 'Returned')),
    PRIMARY KEY (user_id, game_id),
    FOREIGN KEY (user_id) REFERENCES public.user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY (game_id) REFERENCES public.game(game_id)ON DELETE CASCADE ON UPDATE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.game_status
    OWNER to postgres;
