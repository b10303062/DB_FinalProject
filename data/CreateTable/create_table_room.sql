--DROP TABLE IF EXISTS public.room;
CREATE TABLE IF NOT EXISTS public.room (
    Room_id BIGINT NOT NULL PRIMARY KEY,
    Room_name VARCHAR(50) NOT NULL,
	Game_id BIGINT NOT NULL,
	Creator_id BIGINT NOT NULL,
    Start_time timestamp NOT NULL,
    End_time timestamp NOT NULL,
    Status VARCHAR(10) NOT NULL CHECK (Status IN ('Active', 'Closed')),
	MaxPlayers int NOT NULL,	
    FOREIGN KEY (Creator_id) REFERENCES public.USER(User_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Game_id) REFERENCES public.GAME(Game_id) ON DELETE CASCADE ON UPDATE CASCADE
);
