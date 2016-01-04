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
# Unit test for diskstatss plugin
############################################################

import os
import sys
import unittest

from mock import Mock, patch

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import diskstats

# SKU1: 6 disks in sw raid10 config + fioa
PROCFS_DISKSTAT = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               'mocks/proc_diskstats'))
# SKU2: 4 disks in hw raid10 config + ssd
PROCFS_DISKSTAT_2 = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 'mocks/proc_diskstats_2'))

# Expected values for verifications
DEV_LIST = ['sdb', 'sde', 'sdd', 'sdf', 'sdc', 'sda', 'md0', 'md1', 'md2', 'md3', 'fioa']
DEV_LIST_2 = ['sdb', 'sda', 'sda1', 'sda2', 'sda3', 'sda4']

class TestDiskstats(unittest.TestCase):
  def setUp(self):
    diskstats.DISKSTATS_FNAME = PROCFS_DISKSTAT

  def test_1_diskstats_get_dev_list_sku1(self):
    diskstats.get_dev_list()

    try:
      self.assertTrue(len(diskstats.dev_list) > 0, 'at least one metric')
      self.assertEqual(diskstats.dev_list, DEV_LIST, 'device lists parsing error')
    except:
      print('dev_list: %s' % (diskstats.dev_list))
      print('expected DEV_LIST: %s' % (DEV_LIST))
      print('Exception: %s' % (sys.exc_info()[0]))
      raise

  def test_1_diskstats_get_dev_list_sku2(self):
    diskstats.dev_list = []
    diskstats.DISKSTATS_FNAME = PROCFS_DISKSTAT_2
    diskstats.get_dev_list()

    self.assertTrue(len(diskstats.dev_list) > 0, 'at least one metric')
    self.assertEqual(diskstats.dev_list, DEV_LIST_2,
                     'device lists parsing error')

    # restore the default SKU
    diskstats.DISKSTATS_FNAME = PROCFS_DISKSTAT

  def test_2_diskstats_collection(self):
    diskstats.dev_list = []
    diskstats.DISKSTATS_FNAME = PROCFS_DISKSTAT
    diskstats.get_dev_list()
    stats_names = diskstats.diskstat_fields[3:14]
    dev_stats_current = diskstats.collect_diskstats()

    field_names = [dev_stats_current[(diskstats.dev_list[0], k)] for k in
                   stats_names]
    num_dev = len(diskstats.dev_list)
    num_fields = len(field_names)
    num_expected_fields = (num_fields + 1) * num_dev;
    self.assertTrue(len(dev_stats_current) > 0,
                    'at least one metric')
    try:
      self.assertEqual(len(dev_stats_current), num_expected_fields,
                       'unexpected diskstat fields and vals')
    except:
      print('dev_stats_current: %s' % (dev_stats_current))
      print('field_names: %s' % (field_names))
      print('dev_stats_current len: %d' % (len(dev_stats_current)))
      print('Exception: %s' % (sys.exc_info()[0]))
      raise

  def test_3_diskstats_metrics_calc(self):
    diskstats.dev_stats_cache = diskstats.collect_diskstats()
    diskstats.dev_stats_current = diskstats.collect_diskstats()
    metrics_key_vals = diskstats.calc_metrics(diskstats.dev_list[0])
    dev_metrics_vals = metrics_key_vals.values()

    num_metrics_keys = len(diskstats.diskstat_metrics)
    num_metrics_vals = len(dev_metrics_vals)

    try:
      self.assertEqual(num_metrics_keys, num_metrics_vals,
                       'number of metric names not equals to vals')
      self.assertEqual(metrics_key_vals['util_pct'], 0.0, 'wrong util_pct')
      self.assertEqual(metrics_key_vals['bytes_per_write'], None,
                       'wrong bytes_per_write value')
    except:
      print('del_t: %f' % (diskstats.calc_del_t(diskstats.dev_list[0])))
      print('metris_key_vals: %s' % (metrics_key_vals))
      print('Exception: %s' % (sys.exc_info()[0]))
      raise

  def test_4_diskstats_swap_cache(self):
    st_names = diskstats.diskstat_fields[3:14]
    diskstats.dev_stats_cache = diskstats.collect_diskstats()
    diskstats.dev_stats_current = diskstats.collect_diskstats()
    diskstats.swap_current_cache()
    diskstats.dev_stats_current = diskstats.collect_diskstats()

    for i in diskstats.dev_list:
      self.assertNotEqual(diskstats.dev_stats_cache[(i, 'ts')],
                          diskstats.dev_stats_current[(i, 'ts')],
                          'prev and curr timestamps should differ')
      self.assertEqual([diskstats.dev_stats_cache[(i,k)] for k in st_names],
                       [diskstats.dev_stats_current[(i,k)] for k in st_names],
                       'prev and curr dev stats should be same')

if __name__ == '__main__':
  suite = unittest.TestLoader().loadTestsFromTestCase(TestDiskstats)
  unittest.TextTestRunner(verbosity=2).run(suite)
