#! /usr/bin/env python
#
# This is a multi-threaded RBL lookup check for Icinga / Nagios.
# Copyright (C) 2012 Frode Egeland <egeland[at]gmail.com>
#
# Modified by Kumina bv in 2013. We only added an option to use an
# address instead of a hostname.
#
# Modified by Guillaume Subiron (Sysnove) in 2015 : mainly PEP8 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
 
import sys
import os
import getopt
import socket
import string
 
rv = (2, 6)
if rv >= sys.version_info:
    print "ERROR: Requires Python 2.6 or greater"
    sys.exit(3)
 
import Queue
import threading
 
serverlist = [
"aspews.ext.sorbs.net",
"ips.backscatterer.org",
"b.barracudacentral.org",
"l1.bbfh.ext.sorbs.net",
"l2.bbfh.ext.sorbs.net",
"bl.blocklist.de",
"list.blogspambl.com",
"cbl.anti-spam.org.cn",
"cblplus.anti-spam.org.cn",
"cblless.anti-spam.org.cn",
"cdl.anti-spam.org.cn",
"cbl.abuseat.org",
"bogons.cymru.com",
"tor.dan.me.uk",
"torexit.dan.me.uk",
"dnsblchile.org",
"rbl.dns-servicios.com",
"bl.drmx.org",
"dnsbl.dronebl.org",
"rbl.efnet.org",
"bl.emailbasura.org",
"spamsources.fabel.dk",
"dnsbl.cobion.com",
"forbidden.icm.edu.pl",
"spamrbl.imp.ch",
"wormrbl.imp.ch",
"dnsbl.inps.de",
"rbl.interserver.net",
"mail-abuse.blacklist.jippg.org",
"dnsbl.kempt.net",
"bl.konstant.no",
"spamblock.kundenserver.de",
"ubl.lashback.com",
"spamguard.leadmon.net",
"dnsbl.madavi.de",
"service.mailblacklist.com",
"bl.mailspike.net",
"z.mailspike.net",
"rbl.megarbl.net",
"phishing.rbl.msrbl.net",
"spam.rbl.msrbl.net",
"relays.nether.net",
"unsure.nether.net",
"ix.dnsbl.manitu.net",
"psbl.surriel.com",
"dyna.spamrats.com",
"noptr.spamrats.com",
"spam.spamrats.com",
"jp.surbl.org",
"rbl.schulte.org",
"exitnodes.tor.dnsbl.sectoor.de",
"backscatter.spameatingmonkey.net",
"bl.spameatingmonkey.net",
"bl.score.senderscore.com",
"korea.services.net",
"dnsbl.sorbs.net",
"dul.dnsbl.sorbs.net",
"http.dnsbl.sorbs.net",
"misc.dnsbl.sorbs.net",
"new.spam.dnsbl.sorbs.net",
"smtp.dnsbl.sorbs.net",
"socks.dnsbl.sorbs.net",
"spam.dnsbl.sorbs.net",
"web.dnsbl.sorbs.net",
"zombie.dnsbl.sorbs.net",
"bl.spamcannibal.org",
"bl.spamcop.net",
"zen.spamhaus.org",
"l1.spews.dnsbl.sorbs.net",
"l2.spews.dnsbl.sorbs.net",
"dnsrbl.swinog.ch",
"rbl2.triumf.ca",
"truncate.gbudb.net",
"dnsbl-1.uceprotect.net",
"dnsbl-2.uceprotect.net",
"dnsbl-3.uceprotect.net",
"multi.uribl.com",
"virbl.dnsbl.bit.nl",
"dnsbl.zapbl.net",
"dnsbl.webequipped.com",
]
 
####
 
queue = Queue.Queue()
global on_blacklist
on_blacklist = []
 
 
class ThreadRBL(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
 
    def run(self):
        while True:
            # grabs host from queue
            hostname, root_name = self.queue.get()
 
            check_host = "%s.%s" % (hostname, root_name)
            try:
                check_addr = socket.gethostbyname(check_host)
            except socket.error:
                check_addr = None
            if check_addr is not None and "127.0.0." in check_addr:
                on_blacklist.append(root_name)
 
            # signals to queue job is done
            self.queue.task_done()
 
 
def usage(argv0):
    print "%s -w <WARN level> -c <CRIT level> -h <hostname>" % argv0
    print " or"
    print "%s -w <WARN level> -c <CRIT level> -a <ipv4 address>" % argv0
 
 
def main(argv, environ):
    options, remainder = getopt.getopt(argv[1:],
                                       "w:c:h:a:",
                                       ["warn=", "crit=", "host=", "address="])
    status = {'OK': 0, 'WARNING': 1, 'CRITICAL': 2, 'UNKNOWN': 3}
    host = None
    addr = None
 
    if 3 != len(options):
        usage(argv[0])
        sys.exit(status['UNKNOWN'])
 
    for field, val in options:
        if field in ('-w', '--warn'):
            warn_limit = int(val)
        elif field in ('-c', '--crit'):
            crit_limit = int(val)
        elif field in ('-h', '--host'):
            host = val
        elif field in ('-a', '--address'):
            addr = val
        else:
            usage(argv[0])
            sys.exit(status['UNKNOWN'])
 
    if host and addr:
        print "ERROR: Cannot use both host and address, choose one."
        sys.exit(status['UNKNOWN'])
 
    if host:
        try:
            addr = socket.gethostbyname(host)
        except:
            print "ERROR: Host '%s' not found - maybe try a FQDN?" % host
            sys.exit(status['UNKNOWN'])
    addr_parts = string.split(addr, '.')
    addr_parts.reverse()
    check_name = string.join(addr_parts, '.')
    # We set this to make sure the output is nice. It's not used except for the output after this point.
    host = addr
 
# ##### Thread stuff:
 
    # spawn a pool of threads, and pass them queue instance
    for i in range(10):
        t = ThreadRBL(queue)
        t.setDaemon(True)
        t.start()
 
    # populate queue with data
    for blhost in serverlist:
        queue.put((check_name, blhost))
 
    # wait on the queue until everything has been processed
    queue.join()
 
# ##### End Thread stuff
 
    if on_blacklist:
        output = '%s on %s spam blacklists : %s' % (host,
                                                    len(on_blacklist),
                                                    ', '.join(on_blacklist))
        if len(on_blacklist) >= crit_limit:
            print 'CRITICAL: %s' % output
            sys.exit(status['CRITICAL'])
        if len(on_blacklist) >= warn_limit:
            print 'WARNING: %s' % output
            sys.exit(status['WARNING'])
        else:
            print 'OK: %s' % output
            sys.exit(status['OK'])
    else:
        print 'OK: %s not on known spam blacklists' % host
        sys.exit(status['OK'])
 
 
if __name__ == "__main__":
    main(sys.argv, os.environ)
