-- Table: public.friend_with

-- DROP TABLE IF EXISTS public.friend_with;

CREATE TABLE IF NOT EXISTS public.friend_with
(
    user1_id bigint NOT NULL,
    user2_id bigint NOT NULL,
    CONSTRAINT friend_with_pkey PRIMARY KEY (user1_id, user2_id),
    CONSTRAINT friend_with_user1_id_fkey FOREIGN KEY (user1_id)
        REFERENCES public."user" (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT friend_with_user2_id_fkey FOREIGN KEY (user2_id)
        REFERENCES public."user" (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.friend_with
    OWNER to postgres;
