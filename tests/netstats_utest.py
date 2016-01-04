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

############################################################
# Unit test for buddyinfo plugin
############################################################

import os
import sys
import unittest

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import netstats

PROCFS_SNMP = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           'mocks/proc_net_snmp'))
PROCFS_NETSTAT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           'mocks/proc_net_netstat'))

# Expected values for verifications
WHITE_LIST = ['InReceives', 'InHdrErrors', 'ForwDatagrams', 'InDiscards', 'InDelivers', 'OutRequests', 'OutNoRoutes', 'ReasmReqds', 'ReasmOKs', 'ReasmFails', 'InMsgs', 'InErrors', 'InDestUnreachs', 'InEchos', 'InTimestamps', 'InAddrMasks', 'OutMsgs', 'OutDestUnreachs', 'OutEchoReps', 'OutTimestampReps', 'ActiveOpens', 'PassiveOpens', 'AttemptFails', 'EstabResets', 'CurrEstab', 'InSegs', 'OutSegs', 'RetransSegs', 'InErrs', 'OutRsts', 'InDatagrams', 'NoPorts', 'InErrors', 'OutDatagrams', 'RcvbufErrors', 'SndbufErrors', 'SyncookiesFailed', 'EmbryonicRsts', 'TW', 'DelayedACKs', 'DelayedACKLocked', 'DelayedACKLost', 'TCPPrequeued', 'TCPHPHits', 'TCPPureAcks', 'TCPHPAcks', 'TCPLossFailures', 'TCPTimeouts', 'TCPDSACKOldSent', 'TCPAbortOnData', 'TCPAbortOnClose', 'TCPAbortOnTimeout', 'InMcastPkts', 'OutMcastPkts', 'InBcastPkts', 'InOctets', 'OutOctets', 'InMcastOctets', 'OutMcastOctets', 'InBcastOctets']

IP_VALS = ['2', '64', '193667093', '0', '622', '0', '0', '0', '178978597', '8430305', '0', '0', '15', '6026610', '3013266', '15', '0', '0', '0']

class TestNetstats(unittest.TestCase):
  def setUp(self):
    netstats.SNMP_FNAME = PROCFS_SNMP
    netstats.NETSTAT_FNAME = PROCFS_NETSTAT

  def test_1_netstats_get_host_type(self):
    netstats.get_host_type()
    self.assertTrue(netstats.host_type is 'other', 'unknown host type')

  def test_2_netstats_white_list(self):
    netstats.init_snmp_counters_list()
    netstats.init_netstat_counters_list()
    self.assertTrue(len(netstats.ip_list) > 0, 'at least one ip counter')
    self.assertTrue(len(netstats.icmp_list) > 0, 'at least one icmp counter')
    self.assertTrue(len(netstats.tcp_list) > 0, 'at least one tcp counter')
    self.assertTrue(len(netstats.udp_list) > 0, 'at least one udp counter')
    self.assertTrue(len(netstats.tcpext_list) > 0,
                    'at least one tcpext counter')
    self.assertTrue(len(netstats.ipext_list) > 0,
                    'at least one ipext counter')
    self.assertEqual(netstats.white_list, WHITE_LIST,
                     'white lists parsing error')

  def test_3_netstats_collection(self):
    netstats.collect_netstats()
    self.assertTrue(len(netstats.ip_vals) > 0, 'at least one ip counter')
    self.assertTrue(len(netstats.icmp_vals) > 0, 'at least one icmp counter')
    self.assertTrue(len(netstats.tcp_vals) > 0, 'at least one tcp counter')
    self.assertTrue(len(netstats.udp_vals) > 0, 'at least one udp counter')
    self.assertTrue(len(netstats.tcpext_vals) > 0,
                    'at least one tcpext counter')
    self.assertTrue(len(netstats.ipext_vals) > 0,
                    'at least one ipext counter')
    self.assertEqual(netstats.ip_vals, IP_VALS, 'ip counts mis-match')

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TestNetstats)
  unittest.TextTestRunner(verbosity=2).run(suite)
