Черновой вариант работы АнтиЗапрет на OPNSense.

Логика работы: 
- при запросе DNS, если адрес есть в чёрном списке, knot-resolver оптправляет запрос на 127.0.0.4:53, на котором висит dns-proxy.py
- dns-proxy.py запрашивает IP адрес у DNSCrypt-Proxy и добавляет этот адрес в таблицу antizapret и возвращаяет knot-resolver
- весь трафик, подпадающий под адреса в таблице antizapret, отправляется в VPN средствами opnsense

Недостающие компоненты собираются из ports или устанавливаются через pkg install

### Необходимо:

- создать loopback интерфейс 127.0.0.4
- настроить DNSCrypt-Proxy на 127.0.0.1:5353
- создать в firewall aliases таблицу antizapret
- поднять vpn (например, wireguard) и настроить маршрутизацию черезе vpn для адресов назначения из таблицы antizapret
- скопировать содержимое в /root/antizapret/. Из папки opnsense скопировать скрипт запуска dnsproxy в /usr/local/etc/rc.d, добавить запуск в /etc/rc.conf
- настроить knot-resolver
- добавить в планировщик вызов скрипта doall.sh укаждые несколько часов.

### Основано на:

- https://github.com/GubernievS/AntiZapret-VPN-Container
- https://bitbucket.org/anticensority/antizapret-vpn-container
- https://bitbucket.org/anticensority/antizapret-pac-generator-light
- https://github.com/Limych/antizapret/

### Зависимости

- Bash
- cURL
- GNU coreutils
- GNU AWK (gawk)
- sipcalc
- idn
- Python 3.6+
- dnspython 2.0.0+
- ???

### Конфигурационные файлы

- **{in,ex}clude-{hosts,ips}-dist** — конфигурация дистрибутива, предназначена для изменения автором репозитория;
- **{in,ex}clude-{hosts,ips}-custom** — пользовательская конфигурация, предназначена для изменения конечным пользователем скрипта;
- **exclude-regexp-dist.awk** — файл с различным заблокированным «мусором», раздувающим PAC-файл: зеркалами сайтов, неработающими сайтами, и т.д.
- **config.sh** — файл с адресами прокси и прочей конфигурацией.

### Установка и запуск

Склонируйте git-репозиторий, отредактируйте **config/config.sh**, **doall.sh** и **process.sh** под собственные нужды, запустите **doall.sh**.
