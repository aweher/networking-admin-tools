#!/usr/bin/env python

from conf import PEs as pes


def generate_remote_ldp_configuration():
    for pe in pes.keys():
        print(f'####################')
        print(f'# REMOTE LDP Config for {pe}')
        for peer in pes.keys():
            if peer != pe:
                print(f'mpls ldp remote-peer {peer.upper()}')
                print(f' remote-ip {pes[peer]}')

def generate_vpls_configuration(vlanid):
    for pe in pes.keys():
        print('####################')
        print(f'# VPLS config for VLAN{vlanid} to apply in {pe}')
        print(f'vsi vlan{vlanid} static')
        print(f' pwsignal ldp')
        print(f'  vsi-id {vlanid}')
        for peer in pes.keys():
            if peer != pe:
                print(f'  peer {pes[peer]}')