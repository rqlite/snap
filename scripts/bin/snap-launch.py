#! /usr/bin/python3

# Launch instances of rqlite based on /var/snap/rqlite/rqlited.conf

"""Usage: rqlite.launch [start|stop]

Manage rqlited instances based on the configuration file:

  /var/snap/rqlite/common/rqlited.conf

  start      start all instances
  stop       stop all instances

"""
from docopt import docopt
import os, sys, string
import subprocess
import shutil

if __name__ == '__main__':
    arguments = docopt(__doc__)
    if not (arguments['start'] or arguments['stop']):
        print('rqlite.launch: error: indicate start or stop')
        sys.exit()
    print(arguments)

snap_dir = '/var/snap/rqlite/common'
cfg_fn = os.path.join(snap_dir, 'rqlited.conf')
if not os.path.exists(cfg_fn):
    shutil.copy('/snap/rqlite/doc/rqlited.conf.default',
                os.path.join(snap_dir, 'rqlited.conf'))
    print('rqlite.launch: default configuration installed')

config = open(cfg_fn)
instances = []
for line in config.readline():
    if line[:1] == '#': continue
    if line.strip() == '': continue
    # Each line of config specifies service name, service port and raft port
    try:
        (service, port, raft) = line.split()
    except ValueError:
        print('rqlited: skipped: unable to parse "'+line+'"')
        continue
    if not os.path.isdir(os.path.join(snap_dir, 'instances', service)):
        print('rqlited: error: no data directory for "'+service+'", skipped')
        continue
    instances.append({'name': service, 'port': port, 'raft': raft})

# Spawn the individual rqlited instances
for instance in instances:
    pid = subprocess.Popen(['/snap/rqlite/current/bin/rqlited',
        '-http', instance['port'],
        '-raft', instance['raft'],
        os.path.join(snap_dir, 'instances', instance['name'])]).pid

