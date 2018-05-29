Приложение поисковика для Django 2.0. 

Для пагинации нужно установить:
pip3 install django-bootstrap3 

База данных PostgreSQL.
Для переноса данных из файла .csv в таблицу search_search:
\copy search_search(date, links, language, title, h1, h2, h3, h4, h5, h6) FROM '/home/odin/visited_links.csv' DELIMITER ',' CSV;
