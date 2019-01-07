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
**diskstats.py**

This plug-in reads /proc/diskstats and collects stats
for a sub-set of devices, such as sda, sdb, ..., fio,
md0, md1, md2, md3, etc.

In addition to collecting raw stats, plugin can cache
current value to determine time series derivatives (such as, iops, device
utilization, etc.) at next collection interval.

/proc/diskstats output shows one device stats per line and
each line looks like this:

252       1 dm-1 321244 0 12631594 480236 1104086 0 29567992 46637332 0 1841812 47117632

Meaning of these lines is explained in linux kernel
Documentation/iostat.txt (ignores first 3 fileds):

- Field  1 -- # of reads completed
    This is the total number of reads completed successfully.

- Field  2 -- # of reads merged, field 6 -- # of writes merged
    Reads and writes which are adjacent to each other may be merged for
    efficiency.  Thus two 4K reads may become one 8K read before it is
    ultimately handed to the disk, and so it will be counted (and queued)
    as only one I/O.  This field lets you know how often this was done.

- Field  3 -- # of sectors read
    This is the total number of sectors read successfully.

- Field  4 -- # of milliseconds spent reading
    This is the total number of milliseconds spent by all reads (as
    measured from __make_request() to end_that_request_last()).

- Field  5 -- # of writes completed
    This is the total number of writes completed successfully.

- Field  7 -- # of sectors written
    This is the total number of sectors written successfully.

- Field  8 -- # of milliseconds spent writing
    This is the total number of milliseconds spent by all writes (as
    measured from __make_request() to end_that_request_last()).

- Field  9 -- # of I/Os currently in progress
    The only field that should go to zero. Incremented as requests are
    given to appropriate struct request_queue and decremented as they finish.

- Field 10 -- # of milliseconds spent doing I/Os
    This field is increases so long as field 9 is nonzero.

- Field 11 -- weighted # of milliseconds spent doing I/Os
    This field is incremented at each I/O start, I/O completion, I/O
    merge, or read of these stats by the number of I/Os in progress
    (field 9) times the number of milliseconds spent doing I/O since the
    last update of this field.  This can provide an easy measure of both
    I/O completion time and the backlog that may be accumulating.

"""

import collectd
import platform
import socket
import time
import re

### Globals ###
OS_NAME = platform.system()
HOST_NAME = socket.gethostbyaddr(socket.gethostname())[0]

diskstat_fields = ['major', 'minor', 'device',
                   'reads_completed', 'reads_merged',
                   'sectors_read', 'time_spent_reading_ms',
                   'writes_completed', 'writes_merged',
                   'sectors_written', 'time_spent_writing_ms',
                   'inflight_ios', 'io_time_ms',
                   'weighted_time_spent_io']
diskstat_metrics = ['iops_read', 'iops_write', 'iops_rw',
                    'bytes_ps_read', 'bytes_ps_write', 'bytes_ps_rw',
                    'bytes_per_read', 'bytes_per_write', 'bytes_per_rw',
                    'await_read', 'await_write', 'await_rw',
                    'util_pct', 'avgqu_sz', 'svc_tm']
config = {}
dev_list = []
device_filter_regexes = []
filtered_metrics = []

DISKSTATS_FNAME = '/proc/diskstats'
METRIC_PLUGIN = 'diskstats_telemetry'
METRIC_TYPE = 'gauge'
DISK_FILTER = 'DiskFilter'
METRIC_FILTER = 'Filter'

# previous and current stats for derivative metrics
dev_stats_cache = {}
dev_stats_current = {}

# we should get it from /sys/block/fioa/queue/pysical_block_size
dev_blk_sz = 512
one_K = 1024

def get_dev_list():
   if device_filter_regexes is not None and len(device_filter_regexes) > 0:
      get_filtered_dev_list()
   else:
      get_default_dev_list()


def get_filtered_dev_list():
   with open(DISKSTATS_FNAME) as f:
      for line in f:
         fields = line.split()
         fields = [fl.strip() for fl in fields]
         devname = fields[2]
         for regex in device_filter_regexes:
            if re.match(regex, devname):
               dev_list.append(devname)
               continue


def get_default_dev_list():
   """
   This function determines a device list for this plugin monitoring.

   There are a number of non-storage devices in /proc/diskstat output
   that need to be skipped. These inclue loop, ram, and possibly
   other devices and partitions.

   Args:
        None

   Returns:
        Updated global dev_list
   """
   with open(DISKSTATS_FNAME) as f:
      for line in f:
         fields = line.split()
         fields = [fl.strip() for fl in fields]
         is_loop = re.match('^loop', fields[2])
         is_ram = re.match('^ram', fields[2])
         is_sr = re.match('^sr', fields[2])
         is_disk_part = re.findall('(^[hs]d[a-z]+)([\d]+)', fields[2])
         is_raid_md = re.findall('^md[0-9]+', fields[2])
         is_raid_dm = re.findall('^dm-[0-9]+', fields[2])
         if (is_loop) or (is_ram) or (is_sr) or is_disk_part or is_raid_md or is_raid_dm:
             continue
         else:
             dev_list.append(fields[2])

      f.close()

   collectd.info('diskstats get_default_dev_list: dev_list: --- %s\n'
                 % (dev_list))

def init_dev_stats_cache():
   global dev_stats_cache
   dev_stats_cache = collect_diskstats()

def collect_diskstats():
   """
   Collectd statistics for devices in global dev_list from /proc/diskstats

   Args: None

   Returns: A dictionary collection of device specific raw statistics that
            includes timestamps
   """
   device_stats = {}
   with open(DISKSTATS_FNAME) as f:
      for line in f:
         fields = line.split()
         fields = [fl.strip() for fl in fields]
         dev_name = fields[2]
         if any(dev_name in s for s in dev_list):
            for i in range(3, 14):
                device_stats[(dev_name, diskstat_fields[i])] = fields[i]
            device_stats[(dev_name, 'ts')] = time.time()
      f.close()
      return device_stats

def swap_current_cache():
   global dev_stats_cache
   dev_stats_cache = dev_stats_current.copy()

def calc_del_t(dev):
   cur_t = float(dev_stats_current[(dev, 'ts')])
   pre_t = float(dev_stats_cache[(dev, 'ts')])
   del_t = cur_t - pre_t
   return del_t

def calc_metrics(dev):
   # time_delta is in seconds
   time_delta = calc_del_t(dev)

   # read and write operation that actually complete
   cur_r = int(dev_stats_current[(dev, 'reads_completed')])
   pre_r = int(dev_stats_cache[(dev, 'reads_completed')])
   cur_w = int(dev_stats_current[(dev, 'writes_completed')])
   pre_w = int(dev_stats_cache[(dev, 'writes_completed')])

   # read and write blocks
   cur_sec_r = int(dev_stats_current[(dev, 'sectors_read')])
   pre_sec_r = int(dev_stats_cache[(dev, 'sectors_read')])
   cur_sec_w = int(dev_stats_current[(dev, 'sectors_written')])
   pre_sec_w = int(dev_stats_cache[(dev, 'sectors_written')])

   # read and write times in msec. These are 32-bit counters and
   # monotonically increase except on overflow, when they restart
   # from zero.
   cur_t_r = float(dev_stats_current[(dev, 'time_spent_reading_ms')])
   pre_t_r = float(dev_stats_cache[(dev, 'time_spent_reading_ms')])
   cur_t_w = float(dev_stats_current[(dev, 'time_spent_writing_ms')])
   pre_t_w = float(dev_stats_cache[(dev, 'time_spent_writing_ms')])

   # note that io_time_ms is NOT equal to time_spent_reading +
   # time_spent_writing.
   # io_time_ms measures the time device is in use
   cur_t_io = float(dev_stats_current[(dev, 'io_time_ms')])
   pre_t_io = float(dev_stats_cache[(dev, 'io_time_ms')])

   # weighted io times for calculating backlog.
   # Will go to zero on 32-bit counter overflow.
   cur_t_rq = float(dev_stats_current[(dev, 'weighted_time_spent_io')])
   pre_t_rq = float(dev_stats_cache[(dev, 'weighted_time_spent_io')])

   # number of reads and writes
   nr_r = cur_r - pre_r
   nr_w = cur_w - pre_w
   nr_rw = nr_r + nr_w

   # number of sectors read and written
   nr_sec_r = cur_sec_r - pre_sec_r
   nr_sec_w = cur_sec_w - pre_sec_w
   nr_sec_rw = nr_sec_r + nr_sec_w

   # read and write times in seconds
   t_r = (cur_t_r - pre_t_r)/1000.0
   t_w = (cur_t_w - pre_t_w)/1000.0
   t_rw = t_r + t_w
   t_io = (cur_t_io - pre_t_io)/1000.0
   t_rq = (cur_t_rq - pre_t_rq)/1000.0

   # iops
   iops_r = nr_r/time_delta if (nr_r >= 0 and time_delta > 0.0) else None
   iops_w = nr_w/time_delta if (nr_w >= 0 and time_delta > 0.0) else None
   try:
      iops = iops_r + iops_w
   except:
      iops = None

   # read/write bytes/second
   bps_r = (nr_sec_r/time_delta)*dev_blk_sz if (nr_sec_r >= 0 and
                                                time_delta > 0.0) else None
   bps_w = (nr_sec_w/time_delta)*dev_blk_sz if (nr_sec_w >= 0 and
                                                time_delta > 0.0) else None
   try:
      bps = bps_r + bps_w
   except:
      bps = None

   # request sizes in bytes per read, write, and all operations
   sz_r = (nr_sec_r * dev_blk_sz)/(nr_r) if (nr_sec_r >= 0 and
                                             nr_r > 0) else None
   sz_w = (nr_sec_w * dev_blk_sz)/(nr_w) if (nr_sec_w >= 0 and
                                             nr_w > 0) else None
   sz = (nr_sec_rw * dev_blk_sz)/(nr_rw) if (nr_sec_rw >= 0 and
                                             nr_rw > 0) else None

   # average time for read and write operations
   await_r = t_r/nr_r if (t_r >= 0 and nr_r > 0) else None
   await_w = t_w/nr_w if (t_w >= 0 and nr_w > 0) else None
   await_rw = t_rw/nr_rw if (t_rw >= 0 and nr_rw > 0) else None

   # dev utilization as % using ratio of time dev busy in msec to
   # total observation interval in seconds
   util = t_io/time_delta if (t_io >= 0 and time_delta > 0.0) else None
   try:
      util_pct = util * 100.0
   except:
      util_pct = None

   # average queue size = arrival_rate * avg_wait_time (little's law)
   avgqu_sz = t_rq/time_delta if (t_rq >= 0 and time_delta > 0.0) else None

   # average service time using utilization law
   # util = busy_time/total_time = B/T
   #      = (Completions/Completions) * (B/T)
   #      = (C/T)* (B/C)
   #      = throughput * service_time
   try:
      svc_tm = util/iops if (util is not None and iops is not None) else None
   except:
      svc_tm = None

   # return as a key-value dictionary:
   # ['iops_read':iops_r, 'iops_write':iops_w, ... ]
   m = [iops_r, iops_w, iops, bps_r, bps_w, bps, sz_r, sz_w, sz,
        await_r, await_w, await_rw, util_pct, avgqu_sz, svc_tm]
   diskst = dict(zip(diskstat_metrics, m))
   return diskst

def dispatch_metrics(dev_name, keys, vals):
   metric = collectd.Values()
   metric.host = HOST_NAME
   metric.plugin = METRIC_PLUGIN
   metric.type = METRIC_TYPE
   metric.plugin_instance = dev_name

   for i in range(len(keys)):
      if vals[i] is not None:
         if ((filtered_metrics is None) or
             (filtered_metrics is not None and keys[i] in filtered_metrics)):
             metric.type_instance = keys[i]
             metric.values = [vals[i]]
             metric.dispatch()

#=== Callback functions registered with collectd ===#
def configer(c):
   global config, device_filter_regexes, filtered_metrics
   collectd.info('diskstat plugin: configuring host: %s' % (HOST_NAME))

   # Load all configs 
   for child in c.children: 
      config[child.key] = child.values 
 
   if DISK_FILTER not in config: 
      device_filter_regexes = None 
      collectd.info("Since device filter is not defined, metrics for default devices will be published")
   else:
      device_filter_regexes = list(config[DISK_FILTER])
      if len(device_filter_regexes) == 1 and device_filter_regexes[0] == '':
          device_filter_regexes = None
          collectd.info("Device filter is empty string, metrics for default devices will be published")
   collectd.info('Filtered devices are: %s' % (device_filter_regexes))

   if METRIC_FILTER not in config: 
      filtered_metrics = None 
      collectd.info("Since metric filter is not defined, all metrics will be published")
   else:
      filtered_metrics = list(config[METRIC_FILTER])
      if len(filtered_metrics) == 1 and filtered_metrics[0] == '':
          filtered_metrics = None
          collectd.info("Metric filter is empty string, all metrics will be published")
   collectd.info('Filtered metrics are: %s' % (filtered_metrics))

def initer():
   get_dev_list()
   collectd.info('diskstat initer: dev list: %s ' % (dev_list))
   init_dev_stats_cache()
   collectd.info('diskstat init: dev_stats_cache: %s ' % (dev_stats_cache))

def reader(input_data=None):
   global dev_stats_current
   dev_stats_current = collect_diskstats()
   raw_dev_stats_names = diskstat_fields[3:14]

   for i in dev_list:
      raw_dev_stats_vals = [dev_stats_current[(i, k)] for k in
                            raw_dev_stats_names]
      dispatch_metrics(i, raw_dev_stats_names, raw_dev_stats_vals)
      metrics_key_vals = calc_metrics(i)
      dispatch_metrics(i, metrics_key_vals.keys(), metrics_key_vals.values())

   swap_current_cache()

def writer(metric, data=None):
   for i in metric.values:
      collectd.debug("%s (%s): %f" % (metric.plugin, metric.type, i))

def shutdown():
   collectd.info("diskstat plugin shutting down")

#== Callbacks ==#
if (OS_NAME == 'Linux'):
   collectd.register_config(configer)
   collectd.register_init(initer)
   collectd.register_read(reader)
   collectd.register_write(writer)
   collectd.register_shutdown(shutdown)
else:
   collectd.warning('diskstat plugin currently works for Linux only')
