  CREATE TABLE "OPPSC"."DATO_HOLDINGAREA" 
   (	"OPID" NUMBER NOT NULL ENABLE, 
	"VENFLON_R" NUMBER, 
	"VENFLON_L" NUMBER, 
	"INFUSION_RV" NUMBER, 
	"INFUSION_3H" NUMBER, 
	"BEMERKUNG" VARCHAR2(4000 BYTE)
   ) SEGMENT CREATION IMMEDIATE 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 
 NOCOMPRESS LOGGING
  STORAGE(INITIAL 65536 NEXT 1048576 MINEXTENTS 1 MAXEXTENTS 2147483645
  PCTINCREASE 0 FREELISTS 1 FREELIST GROUPS 1
  BUFFER_POOL DEFAULT FLASH_CACHE DEFAULT CELL_FLASH_CACHE DEFAULT)
  TABLESPACE "OPPS_T" ;


  CREATE TABLE "OPPSC"."DATO_HOLDINGAREA_STAFF" 
   (	"DATUM" DATE NOT NULL ENABLE, 
	"OA" VARCHAR2(20 BYTE), 
	"AA" VARCHAR2(20 BYTE), 
	"PFL" VARCHAR2(20 BYTE), 
	 CONSTRAINT "DATO_HOLDINGAREA_STAFF_PK" PRIMARY KEY ("DATUM")
  USING INDEX PCTFREE 10 INITRANS 2 MAXTRANS 255 
  TABLESPACE "OPPS_T"  ENABLE
   ) SEGMENT CREATION DEFERRED 
  PCTFREE 10 PCTUSED 40 INITRANS 1 MAXTRANS 255 
 NOCOMPRESS LOGGING
  TABLESPACE "OPPS_T" ;


