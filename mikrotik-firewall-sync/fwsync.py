#!/usr/bin/env python
# ----------------------------------------
# definimos funciones
def clprint(color,txt,nonl=False):
    if nocolor:
        if nonl:
            print txt,
        else:
            print txt
        return

    colours={
        'default':'',
        'amarillo': '\x1b[01;33m',
        'azul': '\x1b[01;34m',
        'cian': '\x1b[01;36m',
        'verde': '\x1b[01;32m',
        'rojo': '\x1b[01;31m'
    }
    if nonl:
        print colours[color]+txt+'\x1b[00m',
    else:
        print colours[color]+txt+'\x1b[00m'
# -----------------------
def adios(code=0):
    for archivo in mkt_config_pri, mkt_config_sec_nueva, mkt_config_sec_antes, mkt_config_sec_despues:
        try:
            os.remove(archivo)
        except OSError:
            pass
        sys.exit(code)
# ----------------------------------------
def chequeos():
    for router in router_principal, router_secundario:
        noresponde=os.system("ping -c 1 "+router+" > /dev/null 2>&1")

        if noresponde == 0:
            clprint('verde', 'El router '+router+' esta activo...')
        else:
            clprint ('rojo','El router '+router+' no se encuentra activo o no lo puedo pinguear')
            adios(255)
# ----------------------------------------

# inicializacion
import ConfigParser, os, sys, re, time, warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# parsear configuracion
config = ConfigParser.RawConfigParser()
#config.read(__file__[:-3]+'.cfg')
config.read('/etc/fw-sync.cfg')

debug=config.get('sincronizacion','debug')
router_principal=config.get('sincronizacion','router_principal')
router_secundario=config.get('sincronizacion','router_secundario')
router_principal_ident=config.get('sincronizacion','router_principal_ident')
router_secundario_ident=config.get('sincronizacion','router_secundario_ident')
ssh_user=config.get('sincronizacion','ssh_user')
ssh_key_file=config.get('sincronizacion','ssh_key_file')

nocolor='--nocolor' in sys.argv

skip=False

mkt_config_pri=os.tmpnam()
mkt_config_sec_nueva=os.tmpnam()
mkt_config_sec_antes=os.tmpnam()
mkt_config_sec_despues=os.tmpnam()

chequeos()

if debug:
    clprint ('cian','DEBUG: archivo de conf del router principal: '+mkt_config_pri)
    clprint ('cian','DEBUG: archivo de nueva con del router secundario: '+mkt_config_sec_nueva)

clprint('verde', 'Inicio: '+time.strftime("%Y-%m-%d %H:%M:%S"))
clprint('verde', 'Chequeando identidad del router principal...')
current_ident=os.popen('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_principal+' ":put [ /system identity get name ]"').read().strip()
if current_ident=="":
    clprint ('rojo','No puedo obtener la identidad del router')
    adios(255)
if current_ident.lower().startswith(router_secundario_ident):
    clprint ('rojo','La identidad del router principal ('+router_principal+') es la misma que la identidad del router secundario ('+router_secundario+') - '+router_secundario_ident)
    adios(255)
if debug:
    clprint ('cian','\tDEBUG: identidad: '+current_ident)

clprint('verde', 'Creando configuracion de borrado para el router secundario...')
out=open(mkt_config_sec_nueva,'w')

# Eliminar las configs del backup
clprint('verde', 'Agregando los comandos de borrado de firewall...')
for subsection in 'address-list','filter','mangle':
    out.write(":foreach element in=[ /ipv6 firewall "+subsection+" find ] do={ :put [ /ipv6 firewall "+subsection+" remove $element ] }\n")
for subsection in 'address-list','filter','mangle','nat':
    out.write(":foreach element in=[ /ip firewall "+subsection+" find ] do={ :put [ /ip firewall "+subsection+" remove $element ] }\n")
out.write("\n")

clprint('verde', 'Obteniendo la configuracion compacta del router principal ('+router_principal+')')
res=os.system('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_principal+' "/ip fi export compact" 1>'+mkt_config_pri+' 2>/dev/null')
res=os.system('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_principal+' "/ipv6 fi export compact" 1>>'+mkt_config_pri+' 2>/dev/null')
if not res==0:
    clprint ('rojo','El comando devolvio un codigo de error '+str(res))
    adios(255)

clprint('verde', 'Filtrando configuracion...')
cnt=1
for line in open(mkt_config_pri,'r').readlines():
    line=line.strip()
    if re.match('^\/', line):
        skip=False
        if skip: clprint('amarillo','\t- salteando la seccion '+line)
        else: out.write(":put "+str(cnt)+"\n")

    if skip: continue
    out.write(line+"\n")
    cnt+=1

out.write("\n")
out.write("/file remove update-config-script.rsc\n")
out.write("\n")
out.write(":log info \"Configuracion actualizada\"\n")

out.close()

clprint('verde', 'Subiendo configuracion al router secundario ('+router_secundario+')...')
res=os.system('/usr/bin/scp -i '+ssh_key_file+' '+mkt_config_sec_nueva+' '+ssh_user+'@'+router_secundario+':update-config-script.rsc 1>/dev/null 2>/dev/null')
if not res==0:
    clprint ('rojo','El comando devolvio un codigo de error '+str(res))
    adios(255)

clprint('verde', 'Haciendo copia de la configuracion actual del router secundario...')
res=os.system('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_secundario+' "/system backup save name=binary_before_sync_'+time.strftime("%Y_%m_%d")+' dont-encrypt=yes" 1>/dev/null 2>/dev/null')
if not res==0:
    clprint ('rojo','El comando devolvio un codigo de error '+str(res))
    adios(255)

clprint('verde', 'Obteniendo la configuracion actual del router secundario...')
res=os.system('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_secundario+' "/export compact" 1>'+mkt_config_sec_antes+' 2>/dev/null')
if not res==0:
    clprint ('rojo','El comando devolvio un codigo de error '+str(res))
    adios(255)

clprint('verde', 'Corriendo archivo de configuracion...')
res=os.popen('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_secundario+' "/import update-config-script.rsc" | tail -n1').read().strip()
if not res.lower().startswith("script file loaded and executed successfully"):
    clprint ('rojo','El comando devolvio el mensaje "'+str(res)+'"')
    adios(255)

clprint('verde', 'Obteniendo nueva configuracion del router secundario...')
res=os.system('/usr/bin/ssh -x -i '+ssh_key_file+' '+ssh_user+'@'+router_secundario+' "/export compact" 1>'+mkt_config_sec_despues+' 2>/dev/null')
if not res==0:
    clprint ('rojo','El comando devolvio un codigo de error '+str(res))
    adios(255)

clprint('verde', 'Comparando configuraciones...')
clprint('verde', '-----------------------------------------------------------------------')
res=os.system('diff '+mkt_config_sec_antes+' '+mkt_config_sec_despues)
clprint('verde', '-----------------------------------------------------------------------')
adios(0)
