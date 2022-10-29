# Parses a map file, and returns its Spring Name
import zipfile
import py7zr
import lupa

class SmfParseError(Exception):
	pass

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
		raise SmfParseError('Failed to execute mapinfo.lua') from l

	if lupa.lua_type(lua_res) != 'table' or not (
			'modtype' in lua_res and 'version' in lua_res and 'name' in lua_res):
		raise SmfParseError('mapinfo.lua returned data missing required properties')

	if lua_res['modtype'] != 3:
		raise SmfParseError(f'This is not a map, modtype != 3, got {lua_res["modtype"]}')

	mapversion = str(lua_res['version'])
	mapname = lua_res['name']
	if mapname.endswith(mapversion):
		return mapname
	return f"{mapname} {mapversion}"

def get_smfname(filelist):
	for zfile in filelist:
		if 'maps/' in zfile.lower() and zfile.lower().endswith('.smf'):
			return zfile.rpartition('/')[2][:-4]
	raise SmfParseError('failed to find smfname in file list')

# Returns the SpringName of the archive at filepath
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
	raise SmfParseError(f'{filepath} is not a recognized .sdz or .sd7 archive')

if __name__ == "__main__":
	import os
	import sys
	import json
	import traceback
	try:
		springname = pysmf(sys.argv[1])
		print(json.dumps({
			"springname": springname,
			"error": None
		}))
	except:
		print(json.dumps({
			"springname": None,
			"error": f'Error when extracting name: {str(sys.exc_info()[1])}'
		}))
		traceback.print_exc()
		sys.exit(2)
