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

from mock import Mock, patch

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import buddyinfo

PROCFS_BUDDYINFO = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                'mocks/proc_buddyinfo'))

# Expected values for verifications
WHITE_LIST = ['free_pages_4K', 'free_pages_8K', 'free_pages_16K', 'free_pages_32K', 'free_pages_64K', 'free_pages_128K', 'free_pages_256K', 'free_pages_512K', 'free_pages_1024K', 'free_pages_2048K', 'free_pages_4096K']


class TestBuddyinfo(unittest.TestCase):
  def setUp(self):
    buddyinfo.BUDDYINFO_FNAME = PROCFS_BUDDYINFO

  def test_1_buddyinfo_get_host_type(self):
    buddyinfo.get_host_type()
    self.assertTrue(buddyinfo.host_type is 'other', 'unknown host type')

  def test_2_buddyinfo_white_list(self):
    buddyinfo.init_stats_cache()

    self.assertTrue(len(buddyinfo.white_list) > 0, 'at least one metric')
    self.assertEqual(buddyinfo.white_list, WHITE_LIST,
                     'white lists parsing error')

  @patch('collectd.Values')
  def test_3_buddyinfo_collection(self, collectdValues):
    collectdValues.vals = Mock()
    buddyinfo.collect_buddyinfo()

    collectdValues.assert_called_once()
    self.assertTrue(len(buddyinfo.stats_cache) > 0, 'at least one udp counter')

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TestBuddyinfo)
  unittest.TextTestRunner(verbosity=2).run(suite)
