CREATE TABLE IF NOT EXISTS residents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    bp INTEGER
);

INSERT INTO residents (name, age, bp) VALUES ('Hanna', 78, 120);
INSERT INTO residents (name, age, bp) VALUES ('Mary', 82, 155);
INSERT INTO residents (name, age, bp) VALUES ('John', 65, 130);
INSERT INTO residents (name, age, bp) VALUES ('Alice', 90, 140);