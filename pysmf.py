# Parses a map file, and returns its Spring Name
import zipfile
import py7zr
import lupa

def parse_mapinfo(rawmapinfo):
	lua = lupa.LuaRuntime(unpack_returned_tuples = True)
	try:
		lua_func = lua.eval('function ()\n' +
							'local function getfenv() return {} end \n ' +
							'local VFS = {}\n' +
							'VFS.DirList = function () return {} end \n' +
							rawmapinfo + '\n end')
		lua_res = lua_func()
	except lupa.LuaError as l:
		print("Failed to execute mapinfo.lua",str(l))
		return None

	if lua_res['modtype'] != 3:
		print ("This is not a map, modtype != 3")
		return None
	mapversion = lua_res['version']
	mapname = lua_res['name']
	if mapname.endswith(str(mapversion)):
		return mapname
	else:
		return mapname+' ' +str(mapversion)

def get_smfname(filelist):
	for zfile in filelist:
		if 'maps/' in zfile.lower() and zfile.lower().endswith('.smf'):
			return zfile.rpartition('/')[2][:-4]

#Returns the SpringName of the archive at filepath, or None
def pysmf(filepath):
	if filepath.lower().endswith('.sd7'):
		mapfile = py7zr.SevenZipFile(filepath, mode='r')
		if 'mapinfo.lua' in mapfile.getnames(): 
			readfiles = mapfile.read(['mapinfo.lua'])
			mapinfolua = readfiles['mapinfo.lua'].read().decode("utf-8") 
			return parse_mapinfo(mapinfolua)
		else: # look for .smf file
			return get_smfname(mapfile.getnames())
	elif filepath.lower().endswith('.sdz'):
		sdz = zipfile.ZipFile(filepath)
		mapinfopath = zipfile.Path(sdz, at = 'mapinfo.lua') 
		if mapinfopath.is_file():
			mapinfofile = mapinfopath.open(mode = 'rt')
			return parse_mapinfo(mapinfofile.read())
		else: # look for .smf file
			return get_smfname([zipinfo.filename for zipinfo in sdz.infolist()])
	else:
		print(filepath, "is not a recognized .sdz or .sd7 archive")
	return None

if __name__ == "__main__":
	import os
	import sys
	for root, dirs, files in os.walk(os.getcwd() if len(sys.argv)<2 else sys.argv[1]):
		for file in files:
			if file.lower().endswith('.sd7') or file.lower().endswith('.sdz'):
				print(file, pysmf(os.path.join(root,file)))
