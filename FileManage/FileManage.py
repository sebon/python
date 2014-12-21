import sys, time, re, os, glob
import shutil
from time import mktime
from datetime import datetime, timedelta
from operator import itemgetter
import logging
import copy
import pwd, grp # for get file uid gid

logger = logging.getLogger('FileManage')
	
def get_filepath_list(_target_dir_list, symbolic_list, real_list):
	try:
		for _target_dir in _target_dir_list:
			target_dir = os.path.normpath(_target_dir) # remove trailing separator.
			
			for fname in os.listdir(target_dir):
				full_dir = os.path.join(target_dir, fname)
				
				if os.path.isfile(full_dir): # file check
					if os.path.islink(full_dir): # symbolic link file
						symbolic_list.append(full_dir)
						#print 'real path = ' + os.path.realpath (full_dir)
					else:
						if re.search(r'([2][0-9]{3})([0-9]{1,2})([0-3][0-9]).ibd$', fname): # file name is end with YYYYMMDD.ibd 
							real_list.append(full_dir)
	except:
		e = sys.exc_info()[0]
		print 'Exception in get_filepath_list function error = %s' %e

		logger.error( "Exception in get_filepath_list function error = %s" % e )
		sys.exit()

def get_realfilepath_list(_target_dir_list, real_list):
	try:
		for _target_dir in _target_dir_list:
			target_dir = os.path.normpath(_target_dir) # remove trailing separator.
			
			for fname in os.listdir(target_dir):
				full_dir = os.path.join(target_dir, fname)
				
				if os.path.isfile(full_dir): # file check
					if not os.path.islink(full_dir): # NOT symbolic link file
						if re.search(r'([2][0-9]{3})([0-9]{1,2})([0-3][0-9]).ibd$', fname): # file name is end with YYYYMMDD.ibd 
							real_list.append(full_dir)
						#print 'real path = ' + os.path.realpath (full_dir)

	except:
		e = sys.exc_info()[0]
		print 'Exception in get_realfilepath_list function error = %s' %e

		logger.error( "Exception in get_realfilepath_list function error = %s" % e )
		sys.exit()


def get_duedatefileinfo_list(now, limit_day, real_list):
	try:
		duedatefileinfo_dict = {}
		today = now.strftime('%Y%m%d')
		duedate = now -timedelta(days= limit_day)
		print 'today = ' + today
		print 'duedate = %s' % duedate
		#print 'real_list = %s' %real_list
		logger.info('duedate = %s' % duedate);
		for file in real_list:
			file_date = datetime.fromtimestamp(mktime(time.strptime (file[-12:-4], '%Y%m%d')))
					
			if file_date <= duedate: 
				duedatefileinfo_dict[file] = os.path.getsize(file)
		if len(duedatefileinfo_dict )> 0:
			sort_list =sorted(duedatefileinfo_dict.iteritems(), key=itemgetter(1), reverse=True)
			return sort_list		
		else:
			return ''
	except:
		e = sys.exc_info()[0]
		print 'Exception in get_duedatefile_list function error = %s' %e

		logger.error( "Exception in get_duedatefile_list function error = %s" % e )
		sys.exit()


def get_best_path(volume_list , movepath_list):
	try:
		path_list = []
		for volumename in volume_list:
			for pathname in movepath_list:
				if pathname.startswith(volumename[0]):
					path_list.append([pathname, volumename[1]])
		return 

	except:
		e = sys.exc_info()[0]
		print 'Exception in get_best_path function error = %s' %e

		logger.error( "Exception in get_best_path function error = %s" % e )
		sys.exit()


################################################################

def	file_copy(duedatefileinfo_list, volume_list, success_list, fail_list):
	try:
		duedateinfo_len = len(duedatefileinfo_list)
		for i in range(duedateinfo_len):
			#print 'i = %d' %i
			volume_count = len(volume_list)
			volume_index = i%volume_count
			target_info = duedatefileinfo_list[i]
			filename = os.path.basename(target_info[0])
			destination_info = volume_list[volume_index]
			if (destination_info[1] <= 0):
				del volume_list[volume_index]
				
			elif (destination_info[1] > target_info[1]):
				destination = os.path.join(destination_info[0], filename)
				shutil.copy(target_info[0], destination)
				success_list.append({'src':target_info[0] , 'dst':destination})					
				volume_list[volume_index][1] = destination_info[1] - target_info[1]
				#print 'volume_list[volume_index][1] = %d' %volume_list[volume_index][1]
			else:
				for j in range(volume_count):
					destination_info = volume_list[j]
					if (destination_info[1] > target_info[1]):
						destination = os.path.join(destination_info[0], filename)
						shutil.copy(target_info[0], destination)
						success_list.append({'src':target_info[0] , 'dst':destination})					
						volume_list[volume_index][1] = destination_info[1] - target_info[1]

		if (duedateinfo_len > len(success_list)):
			duedatefile_set = set()
			successfile_set = set()
			fail_set = set()
			for duedatefileinfo in duedatefileinfo_list:
				duedatefile_set.add(duedatefileinfo[0])
			for successfileinfo in success_list:
				successfile_set.add(successfileinfo[src])

			fail_set =duedatefile_set - successfile_set
			for fail_path in fail_set:
				fail_list.append(fail_path)
				
		logger.info('success_list =%s' %success_list)
		logger.info('fail_list =%s' %fail_list)

	except:
		e = sys.exc_info()[0]
		print 'Exception in file_copy function error = %s' %e

		logger.error( "Exception in file_copy function error = %s" % e )
		sys.exit()

def make_symboliclink(success_list):
	try:
		for successfile_info in success_list:
			os.remove(successfile_info['src'])
			os.symlink(successfile_info['dst'], successfile_info['src'])
	except:
		e = sys.exc_info()[0]
		print 'Exception in make_symboliclink function error = %s' %e
		logger.error( "Exception in make_symboliclink function error = %s" % e )
		sys.exit()

def set_chown(success_list): # set dest file uid and gid same with src file 
	try:
		for successfile_info in success_list:
			st = os.stat(successfile_info['src'])
			os.chown(successfile_info['dst'], st.st_uid, st.st_gid)
	except:
		e = sys.exc_info()[0]
		print 'Exception in set_chown function error = %s' %e
		logger.error( "Exception in set_chown function error = %s" % e )
		sys.exit()

def get_broken_symlink_realfile(symbolic_list, move_real_list, broken_symlink_list, broken_real_list):
	try:
		symreallink_set = set()
		realfile_set = set(move_real_list)

		for symlink_path in symbolic_list:
			if not (os.path.exists(symlink_path)):
				broken_symlink_list.append(symlink_path)
			else:
				symreallink_set.add(os.path.realpath(symlink_path))
				#print 'symreallink_set' + os.path.realpath(symlink_path)

		broken_real_set = realfile_set - symreallink_set
		for filepath in broken_real_set:
			if re.search(r'([2][0-9]{3})([0-9]{1,2})([0-3][0-9]).ibd$', filepath): # file name is end with YYYYMMDD.ibd 
				broken_real_list.append(filepath)

		logger.info('symbolic link is not exist path (this file will be removed)  = %s' %broken_real_list)
	
	except:
		e = sys.exc_info()[0]
		print 'Exception in get_broken_symlink_realfile function error = %s' %e
		logger.error( "Exception in get_broken_symlink_realfile function error = %s" % e )
		sys.exit()

def removefile(broken_real_list):
	try:
		for remove_file in broken_real_list:
			logger.info('remove_file = %s' %remove_file)
			os.remove(remove_file)
	except:
		e = sys.exc_info()[0]
		print 'Exception in removefile function error = %s' %e

		logger.error( "Exception in removefile function error = %s" % e )
		sys.exit()

def get_diskinfo_list(movepath_list):
	try:
		phydevs = []
		f = open("/proc/filesystems", "r")
		for line in f:
			if not line.startswith("nodev"):
				phydevs.append(line.strip())
	
		retlist = []
		mount_dict = {}
		f = open('/etc/mtab', "r")
		for line in f:
			if not all and line.startswith('none'):
				continue
			fields = line.split()
			mountpoint = fields[1]
			
			st = os.statvfs(mountpoint)
			
			total = (st.f_blocks * st.f_frsize)
			used = (st.f_blocks - st.f_bfree) * st.f_frsize
			free = total*0.9 - used 

			if free > 0 and mountpoint != '/':
				mount_dict[mountpoint]  = free
			else :
				continue

		sort_list =sorted(mount_dict.iteritems(), key=itemgetter(1), reverse=True)
		sort_movepath_list = []

		print 'volume_list = %s' %sort_list
		#print 'movepath_list  = %s' %movepath_list
		for volumeinfo in sort_list:
			for movepath in movepath_list:
				if movepath.startswith(volumeinfo[0]):
					sort_movepath_list.append([movepath, volumeinfo[1]])
					movepath_list.remove(movepath)

		if len(sort_movepath_list)>0:
			return sort_movepath_list
		else :
			return ''
	#for key in sort_list:
	#	volumelist.append(key[0])
	except:
		e = sys.exc_info()[0]
		print 'Exception in get_diskinfo_list error = %s' %e

		logger.error( "Exception in get_diskinfo_list error = %s" % e )
		sys.exit()

def SetParameter(now, main_path, move_path, log_path):	
	try:
		ARGV = sys.argv[1:]

		if len( ARGV ) < 1:
			print 'Please enter the parameter'
			print '-m : main path, -v : move path, -d : limit day, -l : logging path'
			sys.exit()

		for x in ARGV:
			if x.startswith('-m'): # main path
				main_path.append(os.path.normpath(x[2:]))
			elif x.startswith('-v'): # move path
				move_path.append(os.path.normpath(x[2:]))
			elif x.startswith('-d'): # limit date
				global limit_day 
				limit_day = int(x[2:])
				print 'limit_day = ' + str(limit_day)
				#copy.deepcopy(limit_day)
			elif x.startswith('-l'): # log path
				log_path = x[2:]

		#########################################################################
		# path check
		for x in main_path:
			if not(os.path.isdir(x)):
				print 'main path is NOT exist : ' + x
				sys.exit()

		for x in move_path:
			if not(os.path.isdir(x)):
				print 'move path is NOT exist : ' + x
				sys.exit()

		if log_path == '':
			log_path = '.'
		elif not(os.path.isdir(log_path)):
			log_path = '.'
			print 'log path is NOT exist :' + log_path
			sys.exit()

		#########################################################################

		log_path = log_path + '/' +  os.path.split(main_path[0])[1] +'_FileManage_' + now.strftime("%y%m%d") + '.log'
		
		#########################################################################
		# loging path set
		hdlr = logging.FileHandler(log_path)
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(lineno)d:\t %(message)s')
		hdlr.setFormatter(formatter)
		logger.addHandler(hdlr) 
		logger.setLevel(logging.INFO)
		#########################################################################

		#########################################################################
		# print
		print 'main path =  %s' %main_path
		logger.info('main path =  %s' %main_path);
		print 'move path = %s' %move_path
		logger.info('move path = %s' %move_path);

		print 'logfile path : ' + log_path
		logger.info('logfile path : ' + log_path);
		print 'limit day = ' + str(limit_day)
		logger.info('limit day = ' + str(limit_day));
		#########################################################################

	except:
		e = sys.exc_info()[0]
		print 'Exception in  SetParameter functionerror = %s' %e

		sys.exit()

def print_diskinfo(time_flag):
	try:

		print '=============================================='
		print time_flag + ' Disk Info'
		logger.info('==============================================');
		logger.info(time_flag);

		phydevs = []
		f = open("/proc/filesystems", "r")
		for line in f:
			if not line.startswith("nodev"):
			
				phydevs.append(line.strip())
	
		retlist = []
		mount_dict = {}
		f = open('/etc/mtab', "r")
		for line in f:
			if not all and line.startswith('none'):
				continue
			fields = line.split()
			mountpoint = fields[1]
			
			st = os.statvfs(mountpoint)
			free = (st.f_bavail * st.f_frsize)
			print "path = %s" %mountpoint + "\tfree size = %d" %free
			logger.info("path = %s" %mountpoint + "\tfree size = %d" %free);
			
		print '=============================================='
		logger.info('==============================================');
	except:
		e = sys.exc_info()[0]
		print 'Exception in get_diskinfo_list error = %s' %e

		logger.error( "Exception in get_diskinfo_list error = %s" % e )
		sys.exit()

def main() :
	try:
		now = datetime.now()
		st = time.time()
		print now
		mainpath_list = []
		movepath_list = []
		global limit_day # default limit 10 days
		limit_day = 10
		log_path = ''

		SetParameter(now, mainpath_list, movepath_list, log_path) # parameter setting
		
		# start disk info log
		print_diskinfo("START")

		# seperate real file and symbolic file from main path 
		symbolic_list = []
		real_list = []
		get_filepath_list(mainpath_list, symbolic_list, real_list)

		# get file list from move volume path
		move_real_list = []
		get_realfilepath_list(movepath_list, move_real_list)
		
		# check symbolic link is removed compare volume path
		broken_symlink_list = []
		broken_real_list = []
		if len(move_real_list) > 0:
			get_broken_symlink_realfile(symbolic_list, move_real_list, broken_symlink_list, broken_real_list)
			if len(broken_real_list) >0:
				removefile(broken_real_list) # remove file in broken_real_list 
		#print 'move_real_list = %s' %move_real_list
		#print 'broken_symlink_list = %s' %broken_symlink_list
		#print 'broken_real_list = %s' %broken_real_list

		
		# search due date file from real list file. 
		print 'limit day = ' + str(limit_day)
		duedatefileinfo_list = get_duedatefileinfo_list(now, limit_day, real_list)
		if duedatefileinfo_list == '':
			print 'The duedate file is NOT exist'
			logger.info('The duedate file is NOT exist');
			sys.exit()

		#print duedatefileinfo_list
		# get volumelist by free size desc
		volume_list = get_diskinfo_list(movepath_list) 
		if '' == volume_list:
			print 'ERROR : the directroy is NOT exist for file move.'
			sys.exit()	


		# move & make symbolic link 
		success_list = []
		fail_list = []
		file_copy(duedatefileinfo_list, volume_list, success_list, fail_list)
		#print 'success_list = %s' %success_list
		
		if len(success_list) > 0 :
			set_chown(success_list)
			make_symboliclink(success_list)

		et = time.time()
		cost_time  = str(timedelta(seconds=et-st))
		print 'cost time :  %s sec' %cost_time
		logger.info('cost time :  %s sec' %cost_time);

		# END disk info log
		print_diskinfo("END")
		#print 'symbolic_list file : %s' %symbolic_list
		#print 'real_list file : %s' %real_list

	except:
		print 'Exception in  main function'
		sys.exit()

##################################################################################
### Main
##################################################################################
if __name__ == '__main__' :
	try:
		main()
	except:
		print 'Exception in  main'
