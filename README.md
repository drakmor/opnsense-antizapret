Черновой вариант работы АнтиЗапрет на OPNSense.

Недостающие компоненты собираются из ports.

### Необходимо:

- создать loopback интерфейс 127.0.0.4
- настроить DNSCrypt-Proxy на 127.0.0.1:5353
- создать в firewall aliases таблицу antizapret
- поднять vpn (например wireguard) и настроить маршрутизацию черезе vpn для адресов назначения из таблицы antizapret
- скопировать содержимое /root/antizapret/, из папки opnsense соприровать скрипт запуска dnsproxy в /usr/local/etc/rc.d, добавить запуск в /etc/rc.conf
- настроить knot-resolver
- добавить в планировщик вызов скрипта doall.sh укаждые несколько часов.

### Основано на:

https://github.com/GubernievS/AntiZapret-VPN-Container
https://bitbucket.org/anticensority/antizapret-vpn-container
https://bitbucket.org/anticensority/antizapret-pac-generator-light
https://github.com/Limych/antizapret/

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
