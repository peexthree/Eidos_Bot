CREATE TABLE players (uid int, total_spent numeric, xp numeric);
INSERT INTO players VALUES (1, NULL, 100), (2, 10, 200);
SELECT * FROM players WHERE (total_spent, xp) > (SELECT total_spent, xp FROM players WHERE uid = 1);
