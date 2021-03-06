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
# Unit test for zoneinfo plugin
############################################################

import os
import sys
import unittest

from mock import Mock, patch

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import zoneinfo

PROCFS_ZONEINFO = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                'mocks/proc_zoneinfo'))

# Expected values for verifications
WHITE_LIST = ['min', 'low', 'high', 'scanned', 'nr_free_pages', 'nr_dirty', 'nr_writeback', 'nr_vmscan_write', 'nr_anon_transparent_hugepages']


class TestBuddyinfo(unittest.TestCase):
  def setUp(self):
    zoneinfo.ZONEINFO_FNAME = PROCFS_ZONEINFO

  def test_1_zoneinfo_get_host_type(self):
    zoneinfo.get_host_type()
    self.assertTrue(zoneinfo.host_type is 'other', 'unknown host type')

  def test_2_zoneinfo_white_list(self):
    zoneinfo.init_stats_cache()

    self.assertTrue(len(zoneinfo.white_list) > 0, 'at least one metric')
    self.assertEqual(zoneinfo.white_list, WHITE_LIST,
                     'white lists parsing error')

  @patch('collectd.Values')
  def test_3_zoneinfo_collection(self, collectdValues):
    collectdValues.vals = Mock()
    zoneinfo.collect_zoneinfo()

    collectdValues.assert_called_once()
    self.assertTrue(len(zoneinfo.stats_cache) > 0, 'at least one udp counter')

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TestBuddyinfo)
  unittest.TextTestRunner(verbosity=2).run(suite)
