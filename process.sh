#!/usr/local/bin/bash
set -e

#cp result/dnsmasq-aliases-alt.conf /etc/dnsmasq.d/aliases-alt.conf
#service dnsmasq restart

cp result/knot-aliases-alt.conf /usr/local/etc/knot-resolver/knot-aliases-alt.conf
service kresd stop
sleep 3
service kresd start


pfctl -t antizapret -T add -f result/blocked-ranges.txt

#cp result/openvpn-blocked-ranges.txt /etc/openvpn/server/ccd/DEFAULT
#iptables -F azvpnwhitelist
#while read -r line
#do
#    iptables -w -A azvpnwhitelist -d "$line" -j ACCEPT
#done < result/blocked-ranges.txt

#cp result/squid-whitelist-zones.conf /etc/squid/whitelistedhosts.txt
#cp result/iplist_all.txt /etc/squid/whitelistedips.txt
#systemctl reload squid || true

exit 0
