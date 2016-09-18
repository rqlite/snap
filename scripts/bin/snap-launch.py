#! /usr/bin/python3

# Launch instances of rqlite based on /var/snap/rqlite/rqlited.conf

"""Usage: rqlite.launch [start|stop]

Start or stop rqlited instances based on the configuration file:

  /var/snap/rqlite/common/rqlited.conf

  start      start all instances
  stop       stop all instances

"""
from docopt import docopt
import glob, os, sys, string, time
import subprocess, signal, errno
import shutil

# TODO
#  - extract snap paths from env

def get_pid(pid_fn):
    "Retrieve a pid from a pid_file"
    try: pid = int(open(pid_fn).readline())
    except ValueError:
        return None
    return pid

def check_pid(pid):
    """Check whether pid exists. Courtesy StackExchange #568271"""
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True

# Retrieve a set of instances from the config file
def get_instances(snap_dir, cfg_fn):
    instances = []
    instance_dir = os.path.join(snap_dir, 'instances')
    with open(cfg_fn) as config:
        for line in config:
            if line[:1] == '#': continue
            if line.strip() == '': continue
            # Each line of config specifies service name, service port and raft port
            try:
                (service, port, raft) = line.split()
            except ValueError:
                print('rqlited: skipped: unable to parse "'+line+'"')
                continue
            # validate that the service name can be a simple filename
            if not os.path.basename(service) == service:
                print('rqlited: error: unsuitable service name "'+service+'"')
                continue
            if not os.path.isdir(os.path.join(instance_dir, service)):
                print('rqlited: new service "'+service+'"')
            instances.append({'name': service, 'port': port, 'raft': raft})
    return instances



# Spawn the rqlited instances and write pid files
def spawn(instances, instance_dir):
    count = 0
    for instance in instances:
        name, port, raft = instance['name'], instance['port'], instance['raft']
        data_dir = os.path.join(instance_dir, name)
        if not os.path.exists(data_dir):
            try:
                os.mkdir(data_dir)
            except FileExistsError:
                print('rqlited: error: failed to create store for "'+name+'"')
                continue
        # Check if there is a pid file for a running instance
        pid_fn = data_dir+'/pid'
        if os.path.exists(pid_fn):
            pid = get_pid(pid_fn)
            if pid:
                print('rqlite: warning: pid file for "'+name+'" exists.')
                if check_pid(pid):
                    print('rqlite: error: "'+name+'" running, skipped.')
                    continue
        log = open(data_dir+'/log', 'a+')
        instance_proc = subprocess.Popen(['/snap/rqlite/current/bin/rqlited',
            '-http', port, '-raft', raft, data_dir],
            stdout=log, stderr=subprocess.STDOUT)
        pid = instance_proc.pid
        # we'll give it one second to start up and see if it's exited
        # unhappily
        time.sleep(1)
        returncode = instance_proc.poll()
        if returncode != None:
            if returncode == 0:
                print('rqlited: "'+name+'" exited immediately.')
            else:
                print('rqlited: error: "'+name+'" failed to start."')
            continue
        pidfile = open(pid_fn, 'w+')
        pidfile.write(str(pid))
        pidfile.close()
        count += 1
    return count


# Shutdown all instances and remove pid files
def shutdown(instance_dir):
    count = 0
    for pid_file in glob.glob(instance_dir+'/*/pid'):
        instance = os.path.basename(pid_file[:-4])
        pid = get_pid(pid_file)
        if pid == None:
            print('rqlited: error: bad pidfile '+pid_file)
        try:
            os.kill(pid, signal.SIGHUP)
            print('rqlite: stopped "'+instance+'"')
            count += 1
        except ProcessLookupError:
            print('rqlited: error: '+pid_file+' pid not found')
        try: os.remove(pid_file)
        except OSError:
            print('rqlited: error: unable to remove pid file '+pid_file)
    return count


if __name__ == '__main__':
    arguments = docopt(__doc__)
    if not (arguments['start'] or arguments['stop']):
        print('rqlite.launch: error: indicate start or stop')
        sys.exit()

    # Make sure we have a config file or setup the default config
    snap_dir = '/var/snap/rqlite/common'
    cfg_fn = os.path.join(snap_dir, 'rqlited.conf')
    if not os.path.exists(cfg_fn):
        shutil.copy('/snap/rqlite/current/doc/rqlited.conf.default', cfg_fn)
        print('rqlite.launch: default configuration installed')

    # Make sure we have a directory for the instances
    instance_dir = os.path.join(snap_dir, 'instances')
    if not os.path.exists(instance_dir):
        try:
            os.mkdir(instance_dir)
        except FileExistsError:
            print('rqlited: error: unable to create instance directory, done')
            sys.exit(1)

    if arguments['start']:
        instances = get_instances(snap_dir, cfg_fn)
        count = spawn(instances, instance_dir)
        print(str(count)+' instances started')
        sys.exit()

    if arguments['stop']:
        count = shutdown(instance_dir)
        print(str(count)+' instances stopped')
        sys.exit()



