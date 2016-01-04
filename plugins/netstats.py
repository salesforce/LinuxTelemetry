#!/usr/bin/python

##########################################################################
# Copyright (c) 2015, Salesforce.com, Inc.
# All rights reserved.
#
# Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#
# Neither the name of Salesforce.com nor the names of its
# contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##########################################################################

"""
**netstats.py**

This plugin exposes linux network protocol counters
that are available through /proc/net/snmp and
/proc/net/netstat. These protocol counters are typically
examined through netstat (such as, 'netstat -s' command),
which is part of net-tools. While this plugin reads all
available counters, it publishes only a sub-set of them,
which are listed in white_list.

Protocol counter names in /proc/net/snmp and their
meanings:

Ip:
---
- InReceives   : total packets received
- InHdrErrors  : packets received with invalid addresses
- ForwDatagrams: forwarded
- InDiscards   : incoming packets discarded
- InDelivers   : incoming packets delivered
- OutRequests  : requests sent out
- OutNoRoutes  : fragments dropped_after timeout
- ReasmReqds   : reassemblies required
- ReasmOKs     : packets reassembled ok
- ReasmFails   : packet reassembles failed

Icmp:
-----
- InMsgs           : ICMP messages received
- InErrors         : input ICMP message failed
- InDestUnreachs   : destination unreachable
- InTimeExcds      : timeout in transit
- InParmProbs      : wrong parameters'
- InSrcQuenchs     : source quenches
- InRedirects      : redirects
- InEchos          : echo requests
- InEchoReps       : echo replies
- InTimestamps     : timestamp request
- InTimestampReps  : timestamp reply
- InAddrMasks      : address mask request
- InAddrMaskReps   : address mask replies
- OutMsgs          : ICMP messages sent
- OutErrors        : ICMP messages failed
- OutDestUnreachs  : destination unreachable
- OutTimeExcds     : time exceeded
- OutParmProbs     : wrong parameters
- OutSrcQuenchs    : source quench
- OutRedirects     : redirect
- OutEchos         : echo request
- OutEchoReps      : echo replies
- OutTimestamps    : timestamp requests
- OutTimestampReps : timestamp replies
- OutAddrMasks     : address mask requests
- OutAddrMaskReps  : address mask replies']

Tcp:
----
- RtoAlgorithm : TCP retransmission timeout (RTO) algorithm
- RtoMin       : RTO min
- RtoMax       : RTO max
- MaxConn      : Max connections
- ActiveOpens  : active connections openings
- PassiveOpens : passive connection openings
- AttemptFails : failed connection attempts
- EstabResets  : connection resets received
- CurrEstab    : connections established
- InSegs       : segments received
- OutSegs      : segments send out
- RetransSegs  : segments retransmited
- InErrs       : bad segments received
- OutRsts      : resets sent

Udp:
----
- InDatagrams  : packets received
- NoPorts      : packets to unknown port received
- InErrors     : packet receive errors
- OutDatagrams : packets sent
- RcvbufErrors : receive buffer errors
- SndbufErrors : send buffer errors

Protocol counter names in /proc/net/netstat and their
meanings (not an exhaustive list):

Tcpext:
-------
- SyncookiesSent   : SYN cookies sent
- SyncookiesRecv   : SYN cookies received
- SyncookiesFailed : invalid SYN cookies received
- EmbryonicRsts    : resets received for embryonic SYN_RECV sockets
- PruneCalled      : pkts pruned from recv queue because of soc buf overrun
- RcvPruned        : pkts pruned from receive queue
- OfoPruned        : pkts dropped from out-of-order queue because of socket buffer overrun
- OutOfWindowIcmps : ICMP pkts dropped because they were out-of-window
- LockDroppedIcmps : ICMP packets dropped because socket was locked
- TW               : TCP sockets finished time wait in fast timer
- TWRecycled       : time wait sockets recycled by time stamp
- TWKilled         : TCP sockets finished time wait in slow timer
- PAWSPassive      : passive connections rejected because of time stamp
- PAWSActive       : active connections rejected because of time stamp
- PAWSEstab        : pkts rejects in estab connections because of timestamp
- DelayedACKs               : delayed acks sent
- DelayedACKLocked          : delayed acks further delayed because of locked socket
- DelayedACKLost            : times quick ack mode was activated
- ListenOverflows           : times the listen queue of a socket overflowed
- ListenDrops               : SYNs to LISTEN sockets ignored
- TCPPrequeued              : packets directly queued to recvmsg prequeue
- TCPDirectCopyFromBacklog  : packets directly received from backlog
- TCPDirectCopyFromPrequeue : packets directly received from prequeue
- TCPPrequeueDropped        : packets dropped from prequeue
- TCPHPHits                 : packets header predicted
- TCPHPHitsToUser           : packets header predicted and directly queued to user
- TCPPureAcks               : acknowledgments not containing data received
- TCPLossFailures           : TCP data loss events
- TCPTimeouts               : TCP timeout events
- TCPDSACKOldSent           : DSACKs sent for old packets
- TCPAbortOnData            : connections reset due to unexpected data
- TCPAbortOnClose           : connections reset due to early user close
- TCPAbortOnTimeout         : connections aborted due to timeout

Ipext:
------
- InMcastPkts    : multicast packets received
- OutMcastPkts   : multicast packets sent
- InBcastPkts    : broadcast packets received
- InOctets       : octets received
- OutOctets      : octets sent
- InMcastOctets  : multicast octets received
- OutMcastOctets : multicast octets sent
- InBcastOctets  : broadcast octets received

"""

import collectd
import platform
import os
import socket
import time
import re

os_name = platform.system()
host_name = socket.gethostbyaddr(socket.gethostname())[0]
host_types = ['app', 'db', 'ffx', 'indexer', 'search', 'other']
host_type = 'other'

SNMP_FNAME = '/proc/net/snmp'
NETSTAT_FNAME = '/proc/net/netstat'

METRIC_PLUGIN = 'netstats'
METRIC_TYPE = 'gauge'

white_list = [
              # Ip
              'InReceives',
              'InHdrErrors',
              'ForwDatagrams',
              'InDiscards',
              'InDelivers',
              'OutRequests',
              'OutNoRoutes',
              'ReasmReqds',
              'ReasmOKs',
              'ReasmFails',
              # Icmp
              'InMsgs',
              'InErrors',
              'InDestUnreachs',
              'InEchos',
              'InTimestamps',
              'InAddrMasks',
              'OutMsgs',
              'OutDestUnreachs',
              'OutEchoReps',
              'OutTimestampReps',
              # Tcp
              'ActiveOpens',
              'PassiveOpens',
              'AttemptFails',
              'EstabResets',
              'CurrEstab',
              'InSegs',
              'OutSegs',
              'RetransSegs',
              'InErrs',
              'OutRsts',
              # Udp
              'InDatagrams',
              'NoPorts',
              'InErrors',
              'OutDatagrams',
              'RcvbufErrors',
              'SndbufErrors',
              # Tcpext
              'SyncookiesFailed',
              'EmbryonicRsts',
              'TW',
              'DelayedACKs',
              'DelayedACKLocked',
              'DelayedACKLost',
              'TCPPrequeued',
              'TCPHPHits',
              'TCPPureAcks',
              'TCPHPAcks',
              'TCPLossFailures',
              'TCPTimeouts',
              'TCPDSACKOldSent',
              'TCPAbortOnData',
              'TCPAbortOnClose',
              'TCPAbortOnTimeout',
              # Ipext
              'InMcastPkts',
              'OutMcastPkts',
              'InBcastPkts',
              'InOctets',
              'OutOctets',
              'InMcastOctets',
              'OutMcastOctets',
              'InBcastOctets'
              ]

ip_list, ip_vals = [], []
icmp_list, icmp_vals = [], []
icmpmsg_list, icmpmsg_vals = [], []
tcp_list, tcp_vals = [], []
udp_list, udp_vals = [], []
udplite_list, udplite_vals = [], []
tcpext_list, tcpext_vals = [], []
ipext_list, ipext_vals = [], []

re_snmp=re.compile (r'^Ip:\s+(?P<ip_labels>.*)\n'
                    r'^Ip:\s+(?P<ip_vals>.*)\n'
                    r'^Icmp:\s+(?P<icmp_labels>.*)\n'
                    r'^Icmp:\s+(?P<icmp_vals>.*)\n'
                    r'^IcmpMsg:\s+(?P<icmpmsg_labels>.*)\n'
                    r'^IcmpMsg:\s+(?P<icmpmsg_vals>.*)\n'
                    r'^Tcp:\s+(?P<tcp_labels>.*)\n'
                    r'^Tcp:\s+(?P<tcp_vals>.*)\n'
                    r'^Udp:\s+(?P<udp_labels>.*)\n'
                    r'^Udp:\s+(?P<udp_vals>.*)\n'
                    r'^UdpLite:\s+(?P<udplite_labels>.*)\n'
                    r'^UdpLite:\s+(?P<udplite_vals>.*)\n'
                    , re.MULTILINE)

re_netstat=re.compile (r'^TcpExt:\s+(?P<tcpext_labels>.*)\n'
                       r'^TcpExt:\s+(?P<tcpext_vals>.*)\n'
                       r'^IpExt:\s+(?P<ipext_labels>.*)\n'
                       r'^IpExt:\s+(?P<ipext_vals>.*)\n'
                       , re.MULTILINE)

def get_host_type():
   for i in host_types:
      if i in host_name:
         host_type = i

def get_matches(fname, rex):
   match = None
   if os.path.exists(fname):
      with open(fname) as f:
         match = re.finditer(rex, f.read())
      f.close()
   else:
      collectd.error('get_matches: path %s does not exist' % (fname))

   return match

def init_snmp_counters_list():
   global ip_list, icmp_list, icmpmsg_list, tcp_list, udp_list, udplite_list
   match = get_matches(SNMP_FNAME, re_snmp)
   if not match:
      print('init_snmp_white_list: snmp metrics not found')
      return
   for m in match:
      ip_list = m.group('ip_labels').strip().split()
      icmp_list = m.group('icmp_labels').strip().split()
      icmpmsg_list = m.group('icmpmsg_labels').strip().split()
      tcp_list = m.group('tcp_labels').strip().split()
      udp_list = m.group('udp_labels').strip().split()
      udplite_list = m.group('udplite_labels').strip().split()

def init_netstat_counters_list():
   global tcpext_list, ipext_list
   match = get_matches(NETSTAT_FNAME, re_netstat)
   if not match:
      print('init_netstat_white_list: netstat metrics not found')
      return
   for m in match:
      tcpext_list = m.group('tcpext_labels').strip().split()
      ipext_list = m.group('ipext_labels').strip().split()

def init_counters_list():
   init_snmp_counters_list()
   init_netstat_counters_list()

   # print list of found metrics at startup for debugging help
   collectd.info('netstat: ip_list: %s' % (ip_list))
   collectd.info('netstat: icmp_list: %s' % (icmp_list))
   collectd.info('netstat: icmpmsg_list: %s' % (icmpmsg_list))
   collectd.info('netstat: tcp_list: %s' % (tcp_list))
   collectd.info('netstat: udp_list: %s' % (udp_list))
   collectd.info('netstat: udplite_list: %s' % (udplite_list))
   collectd.info('netstat: tcpext_list: %s' % (tcpext_list))
   collectd.info('netstat: ipext_list: %s' % (ipext_list))
   collectd.info('netstat: white_list: %s' % (white_list))

def collect_netstats():
   global ip_vals, icmp_vals, icmpmsg_vals, tcp_vals, udp_vals, udplite_vals
   global tcpext_vals, ipext_vals
   match_snmp = get_matches(SNMP_FNAME, re_snmp)
   if not match_snmp:
      collectd.error('collect_netstat: snmp metrics not found')
      return
   for m in match_snmp:
      ip_vals = m.group('ip_vals').strip().split()
      icmp_vals = m.group('icmp_vals').strip().split()
      icmpmsg_vals = m.group('icmpmsg_vals').strip().split()
      tcp_vals = m.group('tcp_vals').strip().split()
      udp_vals = m.group('udp_vals').strip().split()
      udplite_vals = m.group('udplite_vals').strip().split()

   match_netstat = get_matches(NETSTAT_FNAME, re_netstat)
   if not match_netstat:
      collectd.error('collect_netstat: netstat metrics not found')
      return
   for m in match_netstat:
      tcpext_vals = m.group('tcpext_vals').strip().split()
      ipext_vals = m.group('ipext_vals').strip().split()

def dispatch_metrics(proto, labels, vals):
   metric = collectd.Values()
   metric.host = host_name
   metric.plugin = METRIC_PLUGIN
   metric.plugin_instance = proto
   metric.type = METRIC_TYPE
   for k in range(0, len(labels)):
      if labels[k] in white_list:
         metric.type_instance = labels[k]
         metric.values = [vals[k]]
         metric.dispatch()

#=== Callback functions registered with collectd ===#
def configer(ObjConfiguration):
   collectd.info('netstats plugin: configuring host: %s' % (host_name))

def initer():
   get_host_type()
   collectd.info('netstats plugin: host of type: %s' % (host_type))
   init_counters_list()
   collectd.info('netstats init: white list: %s ' % (white_list))

def reader(input_data=None):
   collect_netstats()

   # dispatch metrics for each protocol seperately
   dispatch_metrics("ip", ip_list, ip_vals)
   dispatch_metrics("icmp", icmp_list, icmp_vals)
   dispatch_metrics("icmp", icmpmsg_list, icmpmsg_vals)
   dispatch_metrics("tcp", tcp_list, tcp_vals)
   dispatch_metrics("udp", udp_list, udp_vals)
   dispatch_metrics("udplite", udplite_list, udplite_vals)
   dispatch_metrics("tcpext", tcpext_list, tcpext_vals)
   dispatch_metrics("ipext", ipext_list, ipext_vals)

def writer(metric, data=None):
   for i in metric.values:
      collectd.debug("%s (%s): %f" % (metric.plugin, metric.type, i))

def shutdown():
   collectd.info("netstats plugin shutting down")

#== Callbacks ==#
if (os_name == 'Linux'):
   collectd.register_config(configer)
   collectd.register_init(initer)
   collectd.register_read(reader)
   collectd.register_write(writer)
   collectd.register_shutdown(shutdown)
else:
   collectd.warning('netstats plugin currently works for Linux only')
