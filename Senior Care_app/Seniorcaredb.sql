-- Create the table
CREATE TABLE IF NOT EXISTS residents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    bp INTEGER
);

INSERT INTO residents (name, age, bp) VALUES ('Hanna', 78, 120);
INSERT INTO residents (name, age, bp) VALUES ('Peter', 82, 155);
INSERT INTO residents (name, age, bp) VALUES ('Mary', 85, 130);
