-- Table: public.user

-- DROP TABLE IF EXISTS public."user";

CREATE TABLE IF NOT EXISTS public."user"
(
    user_id bigint NOT NULL,
    user_name character varying(16) COLLATE pg_catalog."default" NOT NULL,
    email character varying(50) COLLATE pg_catalog."default" NOT NULL,
    password character varying(8) COLLATE pg_catalog."default" NOT NULL,
    join_date date NOT NULL,
    CONSTRAINT "USER_pkey" PRIMARY KEY (user_id),
    CONSTRAINT "USER_email_key" UNIQUE (email)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public."user"
    OWNER to postgres;
