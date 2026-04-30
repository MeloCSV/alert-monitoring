/*==============================================================*/
/* Table: O_EXAMPLES                                              */
/*==============================================================*/

CREATE TABLE public.O_EXAMPLES (
	ID BIGSERIAL NOT NULL,
	CREATION_TIME TIMESTAMP NULL,
	DESCRIPTION VARCHAR(255) NULL,
	IDENTIFICATION VARCHAR(255) NULL,
	IDENTIFICATION_TYPE VARCHAR(3) NULL,
	NAME VARCHAR(255) NULL,
	DAYS_IN_WEEK INT4 NULL,
	CONSTRAINT O_EXAMPLES_PKEY PRIMARY KEY (ID)
);

comment on table O_EXAMPLES is
'Tabla que contiene los ejemplos';

comment on column O_EXAMPLES.ID is
'Código del ejemplo.';

comment on column O_EXAMPLES.CREATION_TIME is
'Fecha de creación del ejemplo.';

comment on column O_EXAMPLES.DESCRIPTION is
'descripción del ejemplo.';

comment on column O_EXAMPLES.IDENTIFICATION is
'Identificación del ejemplo.';

comment on column O_EXAMPLES.IDENTIFICATION_TYPE is
'Tipo de identificación del ejemplo.';

comment on column O_EXAMPLES.NAME is
'Nombre del ejemplo.';

comment on column O_EXAMPLES.DAYS_IN_WEEK is
'Número del día de la semana del ejemplo.';

