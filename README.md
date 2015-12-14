Linux Telemetry Plugins
=======================

This repo provides a number of Collectd plugins for detailed system
 monitoring of a typical Linux server at device and sub-system
levels. These python based plugins extend base collectd to monitor
 disk, flash, RAID, virtual memory, NUMA nodes, memory allocation
 zones, and buddy allocator metrics.

Following plugins are being provided:

1. Diskstats
2. Fusion-io
3. Vmstats
4. Buddyinfo
5. Zoneinfo

Except for fusion-io plugin, all others gather system level metrics
through procfs from corresponding locations: /proc/diskstats,
/proc/vmstats, /proc/buddyinfo, and /proc/zoneinfo.

Installation
------------

Installation process is tested on Red Hat Enterprise Linux Server
release 6.5. It will need to be adapted for other variants of Linux.

###Step 1. Base collectd installation with python:

Base collectd is available from:

https://collectd.org/download.shtml

Current collectd version is 5. There are multiple ways to install including building from source. For
many cloud environments that use Red Hat Enterprise Linux (RHEL), RPM installation will be relevant. Three RPM
packages are needed for all of the above python plugins to work:

1. collectd-5.4.0-105.el6.x86_64
2. libcollectdclient-5.4.0-105.el6.x86_64
3. collectd-python-5.4.0-105.el6.x86_64


Ensure that your yum repo has above three RPMs, which should be
installed by:

`yum --nogpgcheck -y install collectd libcollectdclient collectd-python`

Verify the installation by running

`sudo rpm -qa | grep collectd`,

which should show that above three packages are installed.

For non-RHEL environments or where RPM packages are not available, it is possible to install base collectd directly from source (install any dependencies, such as libtool-ltdl-devel and possibly others depending on system setup, along the way):

```
git clone https://github.com/collectd/collectd.git
cd collectd
./build.sh
./configure --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib --mandir=/usr/share/man --enable-python
make
sudo make install
```

Edit collectd configuration file in /etc/collectd.conf to allow it to use external plugin configurations by adding following lines to it:

```
<Include "/etc/collectd.d">
	Filter "*.conf"
</Include>
```

###Step 2. Installation of telemetry plugins:

Run the install script:

`sudo ./install.sh`

This install script assumes that base collectd installation through
yum resulted in:

1. /etc/collectd.conf
2. /etc/collectd.d (for plugin in conf files)
3. /usr/share/collectd/types.db
4. /usr/share/collectd/plugins/python (for python plugins)

Depending on the RPM packaging, it is not guaranteed that above will
be true in all cases. In those cases, either base installation or
telemetry plugin installation script will require adjustments.


###Step 3. Start/restart collectd:

`service collectd start` (or `restart` if already running)

In case of manual installation from source:

`sudo collectd -C /etc/collectd.conf`


Testing
-------

In order to test the measurements that these plugins gather, enable
CSV plugin from collectd.conf to print the values in text files. You
can choose any one of several available collectd supported tools to forward the
measurements from target hosts to an aggregation point in a cloud
environment for continuous remote monitoring. For instance, Graphite/Carbon can be used for forwarding and visualization of collectd metrics. Collectd comes with wrie_graphite plugin, which can be enabled in collectd.conf to forward metrics to host(s) running Graphite/Carbon as follows:

```
LoadPlugin write_graphite
<Plugin write_graphite>
  <Node "example">
    Host "awaheed-wks"
    Port "2003"
    Protocol "tcp"
    LogSendErrors true
    Prefix "collectd"
    Postfix "collectd"
    StoreRates true
    AlwaysAppendDS false
    EscapeCharacter "_"
  </Node>
</Plugin>
```

Plugins
-------
###Diskstats
This plug-in reads /proc/diskstats and collects stats for devices, such as sda, sdb, ..., fio, md0, md1, md2, md3, etc. In addition to collecting raw stats, plugin can derive metrics such as, iops, device utilization, bytes read/write volumes, queue sizes, service times, etc. at next collection interval.

###Fusion-IO
This  plugin is specifically developed for fusion-io flash device measurement. It currently measures:

1. physical blocks read
2. physical blocks written
3. total blocks
4. min block erases count
5. max block erases count
6. average block erases count

These metrics are extracted from fusion-io command-line utilities: fio-status and fio-get-erase-count.

###Vmstats
This plugin is based on /proc/vmstat raw metrics. In addition to raw metrics, a few metric are derived, which are available through tools such as 'sar' and 'atop':

- pgpgin/s
- pgpgout/s
- fault/s
- majflt/s
- pgfree/s
- pgscank/s
- pgscand/s
- pgsteal/s
- %vmeff

###Buddyinfo
Linux uses buddy allocator for memory management. This plugin is based on number of free pages from /proc/buddyinfo. These free pages statistics are available in terms of NUMA node, allocation zones (such as Normal, DMA, etc.), and order of page sizes: 4K, 8K, 16K, 32K, 64K, 128K, 256K, 512K, 1024K, and 2048K. These statistics are useful for getting a handle on memory pressure, fragmentation, and virtual memory system in-efficiences, and JVM/GC pauses.

###Zoneinfo
This plugin extracts metrics freom /proc/zoneinfo, which essentially breaks down virtual memory stats with respect to each NUMA node and memory zone. It supplements the measurements provided by vmstta and buddyinfo plugins with respect to zones.
