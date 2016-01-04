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
Function test for diskstats plugin regex, parser, and 'iostat 10 1'
emulation with dev metrics over 10 seconds interval. Verify results on
a Linux host using iostat or atop.
"""
import sys
import os
import time
import logging

import collectd
sys.path.append(os.path.join(os.path.dirname(__file__), "../plugins"))
import diskstats


def print_header():
    str = 'Device:            tps    B_read/s     B_wrtn/s'
    print(str)

def dev_pretty_prints(dev, vals):
    st = dev
    for i in range(len(vals)):
        st += ' %20.2f' % vals[i]
    print('%s' % (st))

def main():
    if (diskstats.OS_NAME != 'Linux'):
        print('diskstats plugin currently works for Linux only')
        print('os_name: %s' % (diskstats.os_name))
        print('Finished')
        return

    logging.basicConfig(level=logging.INFO)
    diskstats.get_dev_list()
    diskstats.dev_stats_cache = diskstats.collect_diskstats()
    logging.info('netstats_ftest: dev_list: %s' % (diskstats.dev_list))
    logging.debug('netstats_ftest: dev_stats_cache: %s'
                  % (diskstats.dev_stats_cache))
    print('netstats_ftest: ... sleeping for 10 sec...')
    time.sleep(10)
    diskstats.dev_stats_current = diskstats.collect_diskstats()
    logging.debug('netstats_ftest: dev_stats_cur: %s'
                  % (diskstats.dev_stats_current))
    metric_names = ['iops_rw', 'bytes_ps_read', 'bytes_ps_write']

    print_header()
    metric_key_vals = {}
    metric_vals = []
    for i in diskstats.dev_list:
        metric_key_vals = diskstats.calc_metrics(i)
        logging.debug('metric_key_vals: %s' % (metric_key_vals))
        metric_vals = [metric_key_vals[k] for k in metric_names]
        dev_pretty_prints(i, metric_vals)
        logging.debug('metric_vals: %s' % (metric_vals))

if __name__ == "__main__":
    main()
