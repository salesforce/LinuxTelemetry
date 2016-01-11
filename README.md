Linux Telemetry Plugins
=======================

Linux exposes detailed sub-system and device level statistics through procfs and sysfs. These statistics are useful for system debugging as well as performance tuning. These statistics are often consumed through one-off analysis scripts or a number of command-line tools, such as, vmstat, iostat, netstat, sar, atop, collectl, numastat, and so on. There is a need to capture these statistics 24x7 in a cloud environment to support system health monitoring and alerting, live site incident triage and investigations, performance debugging, and capacity monitoring and planning.

This repo provides a number of Collectd plugins for detailed monitoring of a typical Linux server at device and sub-system
levels. These python based plugins extend base collectd to monitor network, disk, flash, RAID, virtual memory, NUMA nodes, memory allocation zones, and buddy allocator metrics.

Following plugins are being provided:

1. [Diskstats](plugins/diskstats.py)
2. [Fusion-io](plugins/fusionio.py)
3. [Vmstats](plugins/vmstats.py)
4. [Buddyinfo](plugins/buddyinfo.py)
5. [Zoneinfo](plugins/zoneinfo.py)
6. [Netstats](plugins/netstats.py)

Except for fusion-io plugin, all others gather system level metrics through procfs from corresponding locations: /proc/diskstats, /proc/vmstats, /proc/buddyinfo, /proc/zoneinfo, /proc/net/snmp, and /proc/net/netstat.

Installation
------------

Installation process is tested on Red Hat Enterprise Linux Server
release 6.5. It will need to be adapted for other variants of Linux.

###Step 1. Base collectd installation with python:

Base [collectd](https://collectd.org/download.shtml) is available as RPM packages. If yum repo is configured for collectd installation:

`sudo yum install collectd libcollectdclient collectd-python`

For target systems for which RPM packages are not available, it is possible to install base collectd directly from source (install any dependencies, such as libtool-ltdl-devel and possibly others depending on system setup, along the way):

```
git clone https://github.com/collectd/collectd.git
cd collectd
./build.sh
./configure --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib --mandir=/usr/share/man --enable-python
make
sudo make install
sudo cp contrib/redhat/init.d-collectd /etc/init.d/collectd
sudo chmod +x /etc/init.d/collectd
```

Edit collectd configuration in /etc/collectd.conf to allow it to use external plugin configurations by adding following lines to it:

```
<Include "/etc/collectd.d">
	Filter "*.conf"
</Include>
```

###Step 2. Installation of telemetry plugins:

Install plugins using:

`sudo python setup.py install`

This install script requires that base collectd is already installed with
following files/directories:

1. /etc/collectd.conf
2. /etc/collectd.d (for plugin in conf files)
3. /usr/share/collectd/types.db
4. /usr/share/collectd/plugins/python (for python plugins)


###Step 3. Start/restart collectd:

`service collectd start` (or `collectd -C /etc/collectd.conf`)


Testing
-------

In order to test the measurements that these plugins gather, enable
CSV plugin from collectd.conf to print the values in text files.

```
LoadPlugin csv
<Plugin csv>
       DataDir "/var/lib/collectd/csv"
</Plugin>
```

Multiple collectd supported tools can forward measurements from target
hosts to an aggregation point in a cloud environment for continuous remote
monitoring. For instance, Graphite/Carbon can be used for forwarding and
visualization of collectd metrics. Collectd comes with wrie_graphite plugin,
which can be enabled in collectd.conf to forward metrics to host(s) running
Graphite/Carbon as follows:

```
LoadPlugin write_graphite
<Plugin write_graphite>
  <Node "example">
    Host "localhost"
    Port "2003"
    Protocol "tcp"
    LogSendErrors true
    Prefix "Linux"
    Postfix "Telemetry"
    StoreRates true
    AlwaysAppendDS false
    EscapeCharacter "_"
  </Node>
</Plugin>
```

![Linux Telemetry Dashboard](/LinuxTelemetryDashboard.png?raw=true)

Installing Graphite is often a time-consuming process due to complex dependencies. A simpler alternative is to use a Vagrant/VirtualBox guest bundled with Graphite. See for example [this](https://github.com/pkkummermo/grafana-vagrant-puppet-box) implementation.

Plugins
-------
###Diskstats
This plug-in reads /proc/diskstats and collects stats for devices, such as disks, RAID, flash, etc. In addition to collecting raw stats, plugin can derive metrics such as, iops, device utilization, bytes read/write volumes, queue sizes, service times, and so on at next collection interval. These metrics are typically obtained through 'iostat', 'sar', or 'atop'.

###Fusion-IO
This  plugin is specifically developed for fusion-io flash device measurement. It currently measures:

1. physical blocks read
2. physical blocks written
3. total blocks
4. min block erases count
5. max block erases count
6. average block erases count

These metrics are extracted from fusion-io command-line utilities: 'fio-status' and 'fio-get-erase-count'.

###Vmstats
This plugin is based on /proc/vmstat raw metrics. In addition to raw metrics, a few metric are derived, which are available through tools such as 'vmstat', 'sar' and 'atop':

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
Linux uses buddy allocator for memory management. This plugin is based on the number of free pages counters from /proc/buddyinfo. These free pages statistics are available in terms of NUMA node, allocation zones (such as Normal, DMA, etc.), and order of page sizes: 4K, 8K, 16K, 32K, 64K, 128K, 256K, 512K, 1024K, and 2048K. These statistics are useful for getting a handle on memory pressure, fragmentation, and virtual memory system in-efficiences, and JVM/GC pauses. Such statistics are typically obtained from tools such as 'collectl'.

###Zoneinfo
This plugin extracts metrics freom /proc/zoneinfo, which essentially breaks down virtual memory stats with respect to each NUMA node and memory zone. It supplements the measurements provided by vmstta and buddyinfo plugins with respect to zones.

###Netstats
Linux maintains network protocol specific counters under /proc/net/snmp and /proc/net/netstat. Protocols include IP, ICMP, TCP, UDP, and their extensions. This plugin exposes those counters, which are typically available through 'netstat -s' command for net-tools implementation of netstat.
