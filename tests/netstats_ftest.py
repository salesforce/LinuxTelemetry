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
Test for netstat plugin regex, parser, and 'netstat -s'
emulation with interpretation of snmp linux MIB
definitions.
"""

import sys
import os

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import netstats

stats_cache = {}

ip_metrics = [
              ['InReceives', 'total packets received'],
              ['InHdrErrors','with invalid addresses'],
              ['ForwDatagrams','forwarded'],
              ['InDiscards','incoming packets discarded'],
              ['InDelivers','incoming packets delivered'],
              ['OutRequests','requests sent out'],
              ['OutNoRoutes','fragments dropped_after timeout'],
              ['ReasmReqds','reassemblies required'],
              ['ReasmOKs','packets reassembled ok'],
              ['ReasmFails', 'packet reassembles failed']
              ]

icmp_metrics = [
                ['InMsgs', 'ICMP messages received'],
                ['InErrors', 'input ICMP message failed'],
                ['InDestUnreachs', 'destination unreachable'],
                ['InTimeExcds', 'timeout in transit'],
                ['InParmProbs', 'wrong parameters'],
                ['InSrcQuenchs', 'source quenches'],
                ['InRedirects', 'redirects'],
                ['InEchos', 'echo requests'],
                ['InEchoReps', 'echo replies'],
                ['InTimestamps', 'timestamp request'],
                ['InTimestampReps', 'timestamp reply'],
                ['InAddrMasks', 'address mask request'],
                ['InAddrMaskReps', 'address mask replies'],
                ['OutMsgs', 'ICMP messages sent'],
                ['OutErrors', 'ICMP messages failed'],
                ['OutDestUnreachs', 'destination unreachable'],
                ['OutTimeExcds', 'time exceeded'],
                ['OutParmProbs', 'wrong parameters'],
                ['OutSrcQuenchs', 'source quench'],
                ['OutRedirects', 'redirect'],
                ['OutEchos', 'echo request'],
                ['OutEchoReps', 'echo replies'],
                ['OutTimestamps', 'timestamp requests'],
                ['OutTimestampReps', 'timestamp replies'],
                ['OutAddrMasks', 'address mask requests'],
                ['OutAddrMaskReps', 'address mask replies']
                ]

tcp_metrics = [
               ['RtoAlgorithm', 'RTO algorithm'],
               ['RtoMin', 'RTO min'],
               ['RtoMax', 'RTO max'],
               ['MaxConn', 'Max connections'],
               ['ActiveOpens', 'active connections openings'],
               ['PassiveOpens', 'passive connection openings'],
               ['AttemptFails', 'failed connection attempts'],
               ['EstabResets', 'connection resets received'],
               ['CurrEstab', 'connections established'],
               ['InSegs', 'segments received'],
               ['OutSegs', 'segments send out'],
               ['RetransSegs', 'segments retransmited'],
               ['InErrs', 'bad segments received'],
               ['OutRsts', 'resets sent']
               ]
udp_metrics = [
               ['InDatagrams', 'packets received'],
               ['NoPorts', 'packets to unknown port received'],
               ['InErrors', 'packet receive errors'],
               ['OutDatagrams', 'packets sent'],
               ['RcvbufErrors', 'receive buffer errors'],
               ['SndbufErrors', 'send buffer errors']
               ]
tcpext_metrics = [
    ['SyncookiesSent', 'SYN cookies sent'],
    ['SyncookiesRecv', 'SYN cookies received'],
    ['SyncookiesFailed', 'invalid SYN cookies received'],
    ['EmbryonicRsts', 'resets received for embryonic SYN_RECV sockets'],
    ['PruneCalled', 'pkts pruned from recv queue because of soc buf overrun'],
    ['RcvPruned', ' pkts pruned from receive queue'],
    ['OfoPruned', 'pkts dropped from o-o-order queue b/c of sock buf overrun'],
    ['OutOfWindowIcmps', 'ICMP pkts dropped because they were out-of-window'],
    ['LockDroppedIcmps', 'ICMP packets dropped because socket was locked'],
    ['TW', 'TCP sockets finished time wait in fast timer'],
    ['TWRecycled', 'time wait sockets recycled by time stamp'],
    ['TWKilled', 'TCP sockets finished time wait in slow timer'],
    ['PAWSPassive', 'passive connections rejected because of time stamp'],
    ['PAWSActive', 'active connections rejected because of time stamp'],
    ['PAWSEstab', 'pkts rejects in estab connections because of timestamp'],
    ['DelayedACKs', 'delayed acks sent'],
    ['DelayedACKLocked', 'delayed acks further delayed b/c of locked socket'],
    ['DelayedACKLost', 'times quick ack mode was activated'],
    ['ListenOverflows', 'times the listen queue of a socket overflowed'],
    ['ListenDrops', 'SYNs to LISTEN sockets ignored'],
    ['TCPPrequeued', 'packets directly queued to recvmsg prequeue'],
    ['TCPDirectCopyFromBacklog', 'packets directly received from backlog'],
    ['TCPDirectCopyFromPrequeue', 'packets directly received from prequeue'],
    ['TCPPrequeueDropped', 'packets dropped from prequeue'],
    ['TCPHPHits', 'packets header predicted'],
    ['TCPHPHitsToUser', 'packets header predicted and directly queued to user'],
    ['TCPPureAcks', 'acknowledgments not containing data received'],
    ['TCPHPAcks', 'predicted acknowledgments in TCP fast path'],
    ['TCPLossFailures', 'TCP data loss events'],
    ['TCPTimeouts', 'TCP timeout events'],
    ['TCPDSACKOldSent', 'DSACKs sent for old packets'],
    ['TCPAbortOnData', 'connections reset due to unexpected data'],
    ['TCPAbortOnClose', 'connections reset due to early user close'],
    ['TCPAbortOnTimeout', 'connections aborted due to timeout']
    ]

ipext_metrics = [
                 ['InMcastPkts', 'multicast packets received'],
                 ['OutMcastPkts', 'multicast packets sent'],
                 ['InBcastPkts', 'broadcast packets received'],
                 ['InOctets', 'octets received'],
                 ['OutOctets', 'octets sent'],
                 ['InMcastOctets', 'multicast octets received'],
                 ['OutMcastOctets', 'multicast octets sent'],
                 ['InBcastOctets', 'broadcast octets received']
                 ]

def collect_labels_and_stats(proto, labels, vals):
   global stats_cache
   print('\nAll counters for %s:' % (proto))
   for i in range(0, len(labels)):
      stats_cache[(proto, labels[i])] = vals[i]
      print('%s : %s' % (labels[i], vals[i]))

def protocol_pretty_prints(proto, metrics, stats):
   print('\n%s: ' % (proto))
   for i in range(0, len(metrics)):
      val = 'unknown'
      label = metrics[i][0]
      key = (proto, label)
      if key in stats:
         val = stats[key]
      if label in netstats.white_list:
         print('%20s : %50s : %10s'
               % (metrics[i][0],
                  metrics[i][1],
                  val))

def netstats_sum_stats():
   collect_labels_and_stats("ip", netstats.ip_list, netstats.ip_vals)
   collect_labels_and_stats("icmp", netstats.icmp_list, netstats.icmp_vals)
   collect_labels_and_stats("icmpmsg", netstats.icmpmsg_list,
                            netstats.icmpmsg_vals)
   collect_labels_and_stats("tcp", netstats.tcp_list, netstats.tcp_vals)
   collect_labels_and_stats("udp", netstats.udp_list, netstats.udp_vals)
   collect_labels_and_stats("udplite", netstats.udplite_list,
                            netstats.udplite_vals)
   collect_labels_and_stats("tcpext", netstats.tcpext_list,
                            netstats.tcpext_vals)
   collect_labels_and_stats("ipext", netstats.ipext_list, netstats.ipext_vals)

   print('\n\nSummary statistics similar to \'netstat -s\'')
   protocol_pretty_prints('ip', ip_metrics, stats_cache)
   protocol_pretty_prints('icmp', icmp_metrics, stats_cache)
   protocol_pretty_prints('tcp', tcp_metrics, stats_cache)
   protocol_pretty_prints('udp', udp_metrics, stats_cache)
   protocol_pretty_prints('tcpext', tcpext_metrics, stats_cache)
   protocol_pretty_prints('ipext', ipext_metrics, stats_cache)

def main():
   if (netstats.os_name != 'Linux'):
      print('netstat plugin currently works for Linux only')
      print('os_name: %s' % (netstats.os_name))
      print('Finished')
      return

   netstats.initer()
   netstats.collect_netstats()
   netstats_sum_stats()

if __name__ == "__main__":
   main()
