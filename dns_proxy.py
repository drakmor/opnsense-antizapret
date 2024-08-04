#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import struct
from dnslib import DNSRecord, RCODE, QTYPE, A
from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger
import subprocess
import argparse
import time

class ProxyResolver(BaseResolver):
    """
        Proxy resolver - passes all requests to upstream DNS server and
        returns response
    """

    def __init__(self, address, port, timeout, tablename='antizapret'):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.tablename = tablename
        self.ipset = self.load_existing_ips()

    def load_existing_ips(self):
        """
        Load existing IPs from the pf table.
        """
        try:
            output = subprocess.check_output(["pfctl", "-t", self.tablename, "-T", "show"])
            ipset = set(output.decode().splitlines())
            print(f"Loaded {len(ipset)} IPs from the table '{self.tablename}'.")
            return ipset
        except subprocess.CalledProcessError as e:
            print(f"Error loading IPs from table '{self.tablename}': {e}")
            return set()

    def add_real_ip(self, real_addr):
        """
        Add a real IP to the pf table if it is not already present.
        """
        if real_addr in self.ipset:
            print(f"Real addr {real_addr} is already in the list.")
            return True
        
        print(f"Adding real addr {real_addr} to the table '{self.tablename}'.")
        try:
            subprocess.check_call(["pfctl", "-t", self.tablename, "-T", "add", real_addr])
            self.ipset.add(real_addr)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding IP {real_addr} to table '{self.tablename}': {e}")
            return False

    def resolve(self, request, handler):
        try:
            proxy_r = request.send(self.address, self.port, timeout=self.timeout, tcp=(handler.protocol == 'tcp'))
            reply = DNSRecord.parse(proxy_r)

            if request.q.qtype in (QTYPE.AAAA, QTYPE.HTTPS):
                print('GOT AAAA or HTTPS')
                return request.reply()

            if request.q.qtype == QTYPE.A:
                print('GOT A')

                # Filter out CNAME records
                reply.rr = [record for record in reply.rr if record.rtype != QTYPE.CNAME]

                for record in reply.rr:
                    if record.rtype == QTYPE.A:
                        real_addr = str(record.rdata)
                        if not self.add_real_ip(real_addr):
                            reply = request.reply()
                            reply.header.rcode = getattr(RCODE, 'SERVFAIL')
                            return reply
                        record.rname = request.q.qname
                        record.ttl = 300

                return reply

        except socket.timeout:
            reply = request.reply()
            reply.header.rcode = getattr(RCODE, 'NXDOMAIN')

        return reply


class PassthroughDNSHandler(DNSHandler):
    """
        Modify DNSHandler logic (get_reply method) to send directly to
        upstream DNS server rather than decoding/encoding packet and
        passing to Resolver (The request/response packets are still
        parsed and logged but this is not inline)
    """
    def get_reply(self, data):
        host, port = self.server.resolver.address, self.server.resolver.port

        request = DNSRecord.parse(data)
        self.log_request(request)

        response = send_tcp(data, host, port) if self.protocol == 'tcp' else send_udp(data, host, port)

        reply = DNSRecord.parse(response)
        self.log_reply(reply)

        return response


def send_tcp(data, host, port):
    """
        Helper function to send/receive DNS TCP request
        (in/out packets will have prepended TCP length header)
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        sock.sendall(data)
        response = sock.recv(8192)
        length = struct.unpack("!H", bytes(response[:2]))[0]
        while len(response) - 2 < length:
            response += sock.recv(8192)
    return response


def send_udp(data, host, port):
    """
        Helper function to send/receive DNS UDP request
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(data, (host, port))
        response, _ = sock.recvfrom(8192)
    return response


if __name__ == '__main__':
    p = argparse.ArgumentParser(description="DNS Proxy")
    p.add_argument("--port", "-p", type=int, default=53,
                   metavar="<port>",
                   help="Local proxy port (default:53)")
    p.add_argument("--address", "-a", default="",
                   metavar="<address>",
                   help="Local proxy listen address (default:all)")
    p.add_argument("--upstream", "-u", default="8.8.8.8:53",
                   metavar="<dns server:port>",
                   help="Upstream DNS server:port (default:8.8.8.8:53)")
    p.add_argument("--tcp", action='store_true', default=False,
                   help="TCP proxy (default: UDP only)")
    p.add_argument("--timeout", "-o", type=float, default=5,
                   metavar="<timeout>",
                   help="Upstream timeout (default: 5s)")
    p.add_argument("--passthrough", action='store_true', default=False,
                   help="Don't decode/re-encode request/response (default: off)")
    p.add_argument("--log", default="request,reply,truncated,error",
                   help="Log hooks to enable (default: +request,+reply,+truncated,+error,-recv,-send,-data)")
    p.add_argument("--log-prefix", action='store_true', default=False,
                   help="Log prefix (timestamp/handler/resolver) (default: False)")
    args = p.parse_args()

    args.dns, _, args.dns_port = args.upstream.partition(':')
    args.dns_port = int(args.dns_port or 53)

    print("Starting Proxy Resolver (%s:%d -> %s:%d) [%s]" % (
        args.address or "*", args.port,
        args.dns, args.dns_port,
        "UDP/TCP" if args.tcp else "UDP"))

    resolver = ProxyResolver(args.dns, args.dns_port, args.timeout)
    handler = PassthroughDNSHandler if args.passthrough else DNSHandler
    logger = DNSLogger(args.log, args.log_prefix)
    udp_server = DNSServer(resolver,
                           port=args.port,
                           address=args.address,
                           logger=logger,
                           handler=handler)
    udp_server.start_thread()

    if args.tcp:
        tcp_server = DNSServer(resolver,
                               port=args.port,
                               address=args.address,
                               tcp=True,
                               logger=logger,
                               handler=handler)
        tcp_server.start_thread()

    try:
        while udp_server.isAlive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping DNS server...")

