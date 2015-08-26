-- this is a smaple user database
-- passwords are stored as md5 hashes
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE user (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	username TEXT, 
	password TEXT
);

-- default password is "password" (md5 hash)
INSERT INTO "user" VALUES(1,'anaadmin','2a6f7d7166549d0718b8a532012a6eee');
INSERT INTO "user" VALUES(2,'op1','35183a2e4c6b83f428bf7850e2a27879');

DELETE FROM sqlite_sequence;
INSERT INTO "sqlite_sequence" VALUES('user',100);
COMMIT;
