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
INSERT INTO "user" VALUES(1,'admin','5f4dcc3b5aa765d61d8327deb882cf99');

DELETE FROM sqlite_sequence;
INSERT INTO "sqlite_sequence" VALUES('user',1);
COMMIT;
