# Tor-search
Краулер (паук) для сети tor. Собирает на страницах ссылки (внешние и внутринние), а так же html-теги (title, h1, h2, h3, h4, h5, h6).  
Программа написана на python3. Тестировалась на Debian и Ubuntu. На операционной системе должен быть установлен и настроен tor.  
Программа проектировалась под особенности мини-компьютера (orange pi pc): 1 Gb ОЗУ, а в качестве хранилища данных карта microSD.  
В папке откуда будет запускаться программа будут созданы такие файлы:  
 **all_links.csv**  (сюда сохраняются все ссылки найденные среди html-тегов, отсюда же берутся ссылки для дальнейшей работы программы.)   
 **index_start.txt** (сюда сохраняется индекс на ссылки с которого начнет работу программа при следующем старте.)  
 **visited_links.csv** (сюда сохраняются собранные html-теги со страниц которые посетили.)  
 **error.csv** (сохраняются ошибки возникшие во время работы.)   
 **domains_counter.csv** (сюда сохраняются доменны, а также счетчик сколько ссылок принадлежат этому доменну.)   
 **links_from_text.txt** (сюда сохраняются ссылки найденные в тексте страниц, а не среди html-тегов. После проверки на правильность ссылки из этого файла можно добавить в файл all_links.csv.)  

Запускаем программу стандартным спосбом:  
**python3 tor_spider.py**
tor_spider.py -имя файла с кодом программы.

Может потребоваться установка некоторых модулей (через apt-get или через pip). Например:  
**sudo apt-get install python3-pip**  
**sudo apt-get install python3-bs4**  
**sudo apt-get install python3-socks**  
**sudo pip3 install setuptools**  
**sudo pip3 install user_agent**  
**sudo apt-get install python3-lxml**  
