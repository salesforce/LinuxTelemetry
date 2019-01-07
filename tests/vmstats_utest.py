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
# Unit test for vmstats plugin
############################################################

import os
import sys
import unittest

from mock import Mock, patch

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import vmstats

PROCFS_VMSTAT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                'mocks/proc_vmstat'))

# Expected values for verifications
WHITE_LIST = ['nr_free_pages', 'nr_inactive_anon', 'nr_active_anon', 'nr_inactive_file', 'nr_active_file', 'nr_unevictable', 'nr_mlock', 'nr_anon_pages', 'nr_mapped', 'nr_file_pages', 'nr_dirty', 'nr_writeback', 'nr_writeback_temp', 'nr_shmem', 'numa_hit', 'numa_miss', 'numa_foreign', 'numa_interleave', 'numa_local', 'numa_other', 'pgpgin', 'pgpgout', 'pswpin', 'pswpout', 'pgalloc_dma', 'pgalloc_dma32', 'pgalloc_normal', 'pgfault', 'pgmajfault', 'pgsteal_dma', 'pgsteal_dma32', 'pgsteal_normal', 'pgscan_kswapd_dma', 'pgscan_kswapd_dma32', 'pgscan_kswapd_normal', 'pgscan_direct_dma', 'pgscan_direct_dma32', 'pgscan_direct_normal', 'zone_reclaim_failed', 'slabs_scanned', 'kswapd_steal', 'kswapd_inodesteal', 'kswapd_low_wmark_hit_quickly', 'kswapd_high_wmark_hit_quickly', 'kswapd_skip_congestion_wait', 'pageoutrun', 'allocstall', 'pgrotated', 'compact_blocks_moved', 'compact_pages_moved', 'compact_pagemigrate_failed', 'compact_stall', 'compact_fail', 'compact_success', 'htlb_buddy_alloc_success', 'htlb_buddy_alloc_fail']

class TestVmstats(unittest.TestCase):
    def setUp(self):
        vmstats.VMS_FNAME = PROCFS_VMSTAT

    def test_1_vmstats_get_host_type(self):
        vmstats.get_host_type()
        self.assertTrue(vmstats.host_type is 'other', 'unknown host type')

    def test_2_vmstats_white_list(self):
        global WHITE_LIST
        vmstats.init_stats_cache()
        WHITE_LIST = list(set().union(WHITE_LIST,
                                      vmstats.pgsteal_white_list,
                                      vmstats.pgscank_white_list,
                                      vmstats.pgscand_white_list))
        try:
            self.assertTrue(len(vmstats.white_list) > 0, 'at least one metric')
            self.assertEqual(vmstats.white_list, WHITE_LIST, 
                             'white lists parsing error')
        except:
            print('vmstats.white_list: %s' % (vmstats.white_list))
            print('vmstats.pgsteal_white_list: %s' % (vmstats.pgsteal_white_list))
            print('vmstats.pgscank_white_list: %s' % (vmstats.pgscank_white_list))
            print('vmstats.pgscand_white_list: %s' % (vmstats.pgscand_white_list))
            print('expected: %s' % (WHITE_LIST))
            print('size: %d expected: %d'
                  % (len(vmstats.white_list), len(WHITE_LIST)))
            for i in range(len(WHITE_LIST)):
                print('i: %d  %s   -->>     %s' % (i, vmstats.white_list[i], WHITE_LIST[i]))
            print('Exception: %s' % (sys.exc_info()[0]))
            raise

    @patch('collectd.Values')
    def test_3_vmstats_collection(self, collectdValues):
        collectdValues.val = Mock()
        vmstats.collect_vmstats()

        assert collectdValues.call_count == len(WHITE_LIST)
        self.assertTrue(len(vmstats.stats_cache) > 0, 'at least one metric')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVmstats)
    unittest.TextTestRunner(verbosity=2).run(suite)
