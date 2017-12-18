import configparser
from pprint import pprint
import os
import sys
# local classes
from networkdevice import NetworkDevice

config = configparser.ConfigParser()

if os.path.exists('system.cfg'):
    config.read('system.cfg')
else:
    print('Config file needed: system.cfg')
    print('Please make a copy of the example file: system.cfg.default')
    print('Example: cp system.cfg.default system.cfg')
    print('And edit it accordingly before running this script again')
    sys.exit(1)

def check_dirs(dirs):
    """Checks the existence of a list of folders, if they not exists this function will create it"""
    folders=[]
    folders.append(dirs)
    for folder in folders:
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except OSError as e:
            print("Problems with folder {}:".format(str(e)))

# Read all the devices
devices = config.sections()

# Save all configurations
for device in devices:
    dev = NetworkDevice(device, config)
    check_dirs(dev.backupdir)
    conf = dev.extract_config()
    destination = '{}/{}'.format(dev.backupdir, dev.config_name)

    if conf:
        print('Saving configuration for {} in {}'.format(dev.name, destination))
        try:
            with open(destination,'w') as c:
                c.write(str(conf))
        except Exception as e:
            print('Error: '.format(e))
    else:
        print('Error: Configuration for {} was not saved'.format(dev.name))
