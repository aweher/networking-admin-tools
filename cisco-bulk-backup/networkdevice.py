import configparser
from pprint import pprint
import os
import sys
import paramiko
import datetime
import telnetlib
from platform import system as system_name
from os import system as system_call
from netmiko import ConnectHandler

class NetworkDevice:
    """ Managed network device class """

    global connection_timeout
    connection_timeout = 10

    def current_datetime(self):
        td=datetime.datetime
        thedate=td.now()
        return str(thedate.strftime('%Y-%m-%d-%H%M%S'))

    def __init__(self, name, cfg):
        self.name=name
        self.cfg=cfg
        self.ip=cfg[name]['ip']
        self.type=self.cfg['DEFAULT']['device_type']
        self.username=self.cfg['DEFAULT']['auth_username']
        self.password=self.cfg['DEFAULT']['auth_password']
        self.protocol=self.cfg['DEFAULT']['mng_proto']
        self.port=self.cfg['DEFAULT']['mng_port']
        self.pubkey=self.cfg['DEFAULT']['ssh_key_file']
        self.ssh_compress=self.cfg['DEFAULT']['ssh_compression']
        self.backupdir=self.cfg['DEFAULT']['backup_dir']
        self.config_name="{}-{}.txt".format(self.name,self.current_datetime())

        if self.cfg[name]['device_type'] is not None:
            self.type=self.cfg[name]['device_type']

        if self.cfg[name]['auth_username'] is not None:
            self.username=self.cfg[name]['auth_username']

        if self.cfg[name]['auth_password'] is not None:
            self.password=self.cfg[name]['auth_password']

        if self.cfg[name]['mng_proto'] is not None:
            self.protocol=self.cfg[name]['mng_proto']

        if self.cfg[name]['mng_port'] is not None:
            self.port=self.cfg[name]['mng_port']

        if self.cfg[name]['ssh_key_file'] is not None:
            self.pubkey=self.cfg[name]['ssh_key_file']

        if self.cfg[name]['ssh_compression'] is not None:
            self.ssh_compress=self.cfg[name]['ssh_compression']

        if self.cfg[name]['backup_dir'] is not None:
            self.backupdir=self.cfg[name]['backup_dir']

        if not self.is_online():
            print('The device {} ({}) is not online or is not reachable...'.format(self.name, self.ip))

    def is_online(self):
        """ Checks if the device is reachable by UNIX ping """
        qty = 3
        parameters = "-n" if system_name().lower()=="windows" else "-c"
        return system_call("ping {} {} {} > /dev/null 2>&1".format(parameters, qty, self.ip)) == 0

    def cmd_showconfig(self):
        """ Return the command to export the configuration """
        commands = {
            'cisco' : 'show running-config',
            'huawei' : 'display current-configuration',
            'mikrotik' : '/export compact',
        }
        return(commands.get(self.type, "Device type {} not yet supported".format(self.type)))

    def cmd_showdiagnostic(self):
        """ Return the command to diagnose the device status """
        commands = {
            'cisco' : 'show tech-support',
            'huawei' : 'display diagnostic-information',
        }
        return(commands.get(self.type, "Device type {} not yet supported".format(self.type)))

    def extract_config(self):
        """ Extracts the configuration of the device """
        output = ''
        if self.protocol == 'telnet':
            # Connect via TELNET
            print('TELNET protocol is insecure and experimental... Please use SSH')
            try:
                tn = telnetlib.Telnet(self.ip, self.port, connection_timeout)
                if self.type == 'cisco_ios':
                    tn.read_until("Username:")
                    tn.write(self.username+"\n")
                    tn.read_until("Password:")
                    tn.write(self.password+"\n")
                    tn.write("terminal length 0"+"\n")
                    tn.write(self.cmd_showconfig(self)+"\n")
                    tn.write("exit"+"\n")
                    output=tn.read_all()
                    tn.close()
            except Exception as e:
                print('Something went wrong... Please use SSH instead')
                return False

        if self.protocol == 'ssh':
            # Connect via SSH
            cn = ConnectHandler(device_type=self.type,
                                ip=self.ip,
                                username=self.username,
                                password=self.password)
            cn.enable()
            output = cn.send_command(self.cmd_showconfig())
            cn.disconnect()

        return output
