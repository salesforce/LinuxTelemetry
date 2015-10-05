Linux Telemetry Plugins
=================

This repo provides a number of Collectd plugins for detailed system
 monitoring of a typical Linux server at device and sub-system
levels. These phthon based plugins extend base collectd to monitor
 disk, flash, RAID, virtual memory, NUMA nodes, memory allocation
 zones, and buddy allocator metrics.

Following plugins are being provided:
1. Diskstats
2. Fusion-io
3. Vmstats
4. Buffyinfo
5. Zoneinfo

Except for fusion-io plguin, all others gather system level metrics
throgu procfs from corresponding locations: /proc/diskstats,
/proc/vmstats, /proc/buddyinfo, and /proc/zoneinfo.

Installation
----------

Installation process is tested on Red Hat Enterprise Linux Server
release 6.5. It will need to be adapted for other variants of Linux.

1. Base collectd installation with python:
Base collect is available from:
https://collectd.org/download.shtml
Curretn version is 5. There are multiple ways to install including building from source. For
many cloud environments, RPM installation will be relevant. Three RPM
packages are needed for all of the above python plugins to work:

collectd-5.4.0-105.el6.x86_64
libcollectdclient-5.4.0-105.el6.x86_64
collectd-python-5.4.0-105.el6.x86_64


Ensure that your yum repo has above three RPMs, which should be
installed by:

yum --nogpgcheck -y install collectd libcollectdclient collectd-python

Verify the installation by running 'sudo rpm -qa | grep collectd',
which should show above three packages installed.

2. Installation of telemetry plugins:
Run the install script:

sudo ./install.sh

This install script assumes that base collectd installation through
yum results in:
a. /etc/collectd.conf
b. /etc/collectd.d (for plugin in conf files)
c. /usr/share/collectd/types.db
d. /usr/share/collectd/plugins/python (for python plugins)

Depending on the RPM packaging, it is not guaranteed that above will
be true in all cases. In that case, either base installation or
telemetry plugin installation script will require adjustments.


3. Start/restart collectd:
service collectd start (or restart if already running)

In order to test the measurements that these plugins gather, enable
CSV plugin from collectd.conf to print the values in text files. You
can choose any one of several available collectd supported tools to forward the
measurements from target hosts to an aggregation point in a cloud
environment for continuous remote monitoring.

Plugin specific information is available in plugins .py files.

