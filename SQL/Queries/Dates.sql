-- All rows before October 1, 2003
SELECT title, author, proper_date
FROM Books
WHERE proper_date < '2003-10-01';
