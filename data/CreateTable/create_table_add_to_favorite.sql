CREATE TABLE IF NOT EXISTS public.ADD_TO_FAVORITE (
    User_id BIGINT NOT NULL,
    Game_id BIGINT NOT NULL,
    PRIMARY KEY (User_id, Game_id),
    FOREIGN KEY (User_id) REFERENCES public.USER(User_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    FOREIGN KEY (Game_id) REFERENCES public.GAME(Game_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);
