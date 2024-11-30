-- Table: public.user_in_room

-- DROP TABLE IF EXISTS public.user_in_room;

CREATE TABLE IF NOT EXISTS public.user_in_room
(
    user_id bigint NOT NULL,
    room_id bigint NOT NULL,
    join_time timestamp without time zone NOT NULL,
    leave_time timestamp without time zone NOT NULL,
    CONSTRAINT user_in_room_pkey PRIMARY KEY (user_id, room_id),
    CONSTRAINT fk_room FOREIGN KEY (room_id)
        REFERENCES public.room (room_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES public."user" (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_in_room
    OWNER to postgres;
