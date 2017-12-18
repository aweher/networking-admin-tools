#!/usr/bin/env python
from __builtin__ import True
from ConfigParser import NoOptionError, NoSectionError

# Hecho por Ariel Weher <ariel@weher.net> @20150406

# ----------------------------------------
# definimos funciones
def clprint(color,txt,nonl=False):
	if nocolor:
		if nonl:
			print txt,
		else:
			print txt+'\n'
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
		print colours[color]+txt+'\x1b[00m'+'\n',
# -----------------------
def adios(code=0):
	try:
		os.remove(mkt_config)
	except OSError:
		pass
	sys.exit(code)
# ----------------------------------------
def icmptest(routerhost):
	noresponde=os.system("ping -c 3 "+routerhost+" > /dev/null 2>&1")

	if noresponde == 0:
		clprint('verde', 'El router '+routerhost+' esta activo...')
		return True
	else:
		clprint ('rojo','El router '+routerhost+' no se encuentra activo o no lo puedo pinguear')
		return False
# ----------------------------------------
def sshcmd(conf,comando):
	if not conf['sshprivatekey'] == '' and os.path.exists(conf['sshprivatekey']):
		try:
			s = ssh.Connection(conf['direccion'],conf['sshuser'],conf['sshprivatekey'], None, conf['sshport'])
		except Exception as e:
			clprint('rojo','ERROR: No pude conectar al host '+conf['sshuser']+'@'+conf['direccion']+':'+conf['sshport']+' usando la clave publica '+conf['sshprivatekey'])
			clprint('rojo',str(e))
			pass
	else:
			try:
				s = ssh.Connection(conf['direccion'],conf['sshuser'], None, conf['sshpassword'], int(conf['sshport']))
			except Exception as e:
				clprint('rojo','ERROR: No pude conectar al host '+conf['sshuser']+'@'+conf['direccion']+':'+conf['sshport']+' usando el password '+conf['sshpassword'])
				clprint('rojo',str(e))
	result=s.execute(comando)
	s.close()
	return result
# ----------------------------------------
def sshget(conf):
	archivo = conf['archivo']+'.rsc'
	if not conf['sshprivatekey'] == '' and os.path.exists(conf['sshprivatekey']):
		try:
			s = ssh.Connection(conf['direccion'],conf['sshuser'],conf['sshprivatekey'], None, conf['sshport'])
		except Exception as e:
			clprint('rojo','ERROR: No pude conectar al host '+conf['sshuser']+'@'+conf['direccion']+':'+conf['sshport']+' usando la clave publica '+conf['sshprivatekey'])
			clprint('rojo',str(e))
			pass
	else:
			try:
				s = ssh.Connection(conf['direccion'],conf['sshuser'], None, conf['sshpassword'], int(conf['sshport']))
			except Exception as e:
				clprint('rojo','ERROR: No pude conectar al host '+conf['sshuser']+'@'+conf['direccion']+':'+conf['sshport']+' usando el password '+conf['sshpassword'])
				clprint('rojo',str(e))
	result=s.get(archivo, conf['store']+archivo)
	s.close()
	return result
# ----------------------------------------
def foldercheck(directorio):
	try:
		if not os.path.exists(directorio):
			os.makedirs(directorio)
	except OSError as e:
		clprint('rojo','Problemas con la carpeta '+directorio+': '+str(e))
# ----------------------------------------
# inicializacion
import ConfigParser, os, sys, re, time, warnings, ast, ssh
warnings.filterwarnings("ignore", category=RuntimeWarning)

nocolor='--nocolor' in sys.argv
hostconf=dict()

# parsear configuracion
config = ConfigParser.RawConfigParser()
try:
	config.read('mkt-backup.cfg')
except error as e:
	clprint('rojo','Error al leer el archivo de configuracion mkt-backup.cfg: '+str(e))

for router in config.sections():
	hostconf.clear()
	hostconf['debug']=''
	hostconf['direccion']=''
	hostconf['sshuser']=''
	hostconf['sshpassword']=''
	hostconf['sshprivatekey']=''
	hostconf['sshport']=''
	hostconf['backupdir']=''
	hostconf['identity']=router
	hostconf['fechahora']=time.strftime("%Y%m%d-%H%M%S")
	hostconf['archivo']=hostconf['identity']+'-'+hostconf['fechahora']
	if re.search('^mikrotik-',router):
		clprint('cian','DEBUG: Encontre una configuracion para el router: '+str(router))
 		try:
			hostconf['debug']=config.get(router,'debug')
			hostconf['direccion']=config.get(router,'ip')
			if (hostconf['direccion'] == ""):
				hostconf['direccion'] = router #probamos que el hostname sea la ip
			if (icmptest(hostconf['direccion']) == False):
				continue
			hostconf['sshuser']=config.get(router,'ssh_user')+'+nc'
			if (config.get(router,'ssh_user') == ''):
				hostconf['sshuser'] = 'admin+nc'
			hostconf['sshprivatekey']=config.get(router,'ssh_key_file')
			hostconf['sshpassword']=config.get(router,'ssh_password')
			hostconf['sshport']=config.get(router,'ssh_port')
			if (hostconf['sshport']==''):
				hostconf['sshport']=22
			hostconf['backupdir']=config.get(router,'backupdir')	
   		except (NoSectionError, NoOptionError) as e:
   			clprint('amarillo','WARN: '+str(e)+' on configuration file')
   			pass
		
		if (hostconf['backupdir']==''):
			hostconf['backupdir']='./backups'

		hostconf['store']=hostconf['backupdir']+'/'+hostconf['identity']+'/'
		
		foldercheck(hostconf['backupdir'])			
		foldercheck(hostconf['store'])
 		
 		lineas = sshcmd(hostconf,':put [ /system identity get name ]')
 		if hostconf['debug'] == True:
 			clprint('cian','DEBUG: Pidiendo al router que haga un export compacto (puede tardar bastante)...')
 			clprint('cian','DEBUG: '+hostconf['fechahora'])
 		sshcmd(hostconf,':put [ /export compact file='+hostconf['archivo']+' ]')

 		if hostconf['debug']:
			clprint('cian','DEBUG: Obteniendo el archivo de backup desde el router...')
			clprint('cian','DEBUG: '+hostconf['archivo']+' --> '+hostconf['store'])
		sshget(hostconf)
		
