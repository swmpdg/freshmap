from random import randint

from point import *
from tex import *

# boilerplate at top of file
class Vmf:
	# template for outputting a "side"
	side_tpl = """\t\tside
		{
			"id" "%d"
			"plane" "(%f %f %f) (%f %f %f) (%f %f %f)"
			"material" "%s"
			"uaxis" "[%f %f %f %f] %f"
			"vaxis" "[%f %f %f %f] %f"
			"rotation" "%f"
			"lightmapscale" "16"
			"smoothing_groups" "0"
"""
	side_end = "\t\t}\n"

	def __init__(self, filename):
		self.num = 1
		self.f = open(filename, 'w')
		data = """versioninfo
{
	"editorversion" "400"
	"editorbuild" "5454"
	"mapversion" "2"
	"formatversion" "100"
	"prefab" "0"
}
visgroups
{
}
viewsettings
{
	"bSnapToGrid" "1"
	"bShowGrid" "1"
	"bShowLogicalGrid" "0"
	"nGridSpacing" "32"
	"bShow3DGrid" "0"
}
"""
		self.f.write(data)

	# start writing the worldspawn
	def worldspawn(self):
		data = """world
{
	"id" "%d"
	"mapversion" "2"
	"classname" "worldspawn"
	"detailmaterial" "detail/detailsprites"
	"detailvbsp" "detail.vbsp"
	"maxpropscreenwidth" "-1"
	"musicpostfix" "Waterfront"
	"skyname" "sky_l4d_rural02_hdr"
"""
		self.f.write(data % self.num)
		self.num += 1

	# start outputting a solid
	def solid(self):
		data = '\tsolid\n\t{\n\t\t"id" "%d"\n'
		self.f.write(data % self.num)
		self.num += 1

	def end_solid(self):
		self.f.write('\t}\n')

	# write a solid axis-aligned block in an entity or the worldspawn
	def block(self, block, tex, displacement=None, autofit=True):
		self.solid()

		a = Point( block.z1, block.y1, block.x0 )
		b = Point( block.z1, block.y1, block.x1 )
		c = Point( block.z1, block.y0, block.x1 )
		d = Point( block.z0, block.y0, block.x0 )
		e = Point( block.z0, block.y0, block.x1 )
		f = Point( block.z0, block.y1, block.x1 )
		g = Point( block.z1, block.y0, block.x0 )
		h = Point( block.z0, block.y1, block.x0 )

		#      point a         uaxis            vaxis              rotation
		#      |  point b      |      ushift    |        vshift    |
		#      |  |  point c   |      |  uscale |        |  vscale |
		#      |  |  |         |      |  |      |        |  |      |
		ls = [[a, b, c,  tex, (1,0,0, 0, 0.25,  0,-1, 0, 0, 0.25), 0],
		      [d, e, f,  tex, (1,0,0, 0, 0.25,  0,-1, 0, 0, 0.25), 0],
		      [a, g, d,  tex, (0,1,0, 0, 0.25,  0, 0,-1, 0, 0.25), 0],
		      [f, e, c,  tex, (0,1,0, 0, 0.25,  0, 0,-1, 0, 0.25), 0],
		      [b, a, h,  tex, (1,0,0, 0, 0.25,  0, 0,-1, 0, 0.25), 0],
		      [e, d, g,  tex, (1,0,0, 0, 0.25,  0, 0,-1, 0, 0.25), 0]]

		sidenum = 0
		for a,b,c,tex,deffit,rot in ls:
			plane = (a.x,a.y,a.z, b.x,b.y,b.z, c.x,c.y,c.z, tex)
			if autofit: deffit = texfit(a,b,c,tex)
			side = (self.num,) + plane + deffit + (rot,)
			self.num += 1

			self.f.write( self.side_tpl % side )

			if displacement and displacement.sidenum==sidenum:
				self.displace(displacement,side[1],side[8],side[9])

			self.f.write( self.side_end )
			sidenum += 1
		self.end_solid()

	# output a solid pyramid
	# base should be a list of Point()s
	def pyramid(self, base, height, basetex, facetex):
		self.solid()

		a,b,c,d = base
		center = (a+b+c+d) * 0.25
		hvec = crossproduct(b-a,d-a)
		normalize(hvec)
		t = hvec * height + center # t is pyramid tip
		ls = [[a, b, c, basetex],
		      [t, b, a, facetex],
		      [t, c, b, facetex],
		      [t, d, c, facetex],
		      [t, a, d, facetex]]

		for a,b,c,tex in ls:
			plane = (a.x,a.y,a.z, b.x,b.y,b.z, c.x,c.y,c.z, tex)
			side = (self.num,) + plane + texfit(a,b,c,tex) + (0,)
			self.num += 1
			self.f.write( self.side_tpl % side )
			self.f.write( self.side_end )

		self.end_solid()

	# output displacement information
	def displace(self,dis,startx,starty,startz):
		n = dis.nverts

		data = """			dispinfo
			{
				"power" "%d"
				"startposition" "[%d %d %d]"
				"flags" "0"
				"elevation" "0"
				"subdiv" "0"
				normals
				{
"""
		self.f.write(data % (dis.power, startx,starty,startz))

		#output normals
		for i in range(n):
			self.f.write('\t\t\t\t\t"row%d" "' % i)
			self.f.write(' '.join( n*["0 0 1"] ))
			self.f.write('"\n')

		#close normals, open distances
		self.f.write("\t\t\t\t}\n\t\t\t\tdistances\n\t\t\t\t{\n")

		#output distances
		for i in range(n):
			self.f.write('\t\t\t\t\t"row%d" "' % i)
			self.f.write(' '.join( [str(x) for x in dis.dists[n*i:n*(i+1)]] ))
			self.f.write('"\n')

		#close distances, open alphas
		self.f.write("\t\t\t\t}\n\t\t\t\talphas\n\t\t\t\t{\n")

		#output alphas
		for i in range(n):
			self.f.write('\t\t\t\t\t"row%d" "' % i)
			self.f.write(' '.join( [str(x) for x in dis.alphas[n*i:n*(i+1)]] ))
			self.f.write('"\n')

		#close alphas, close dispinfo
		self.f.write("\t\t\t\t}\n\t\t\t}\n")

	# end of any entity or the worldspawn
	def end_ent(self):
		self.f.write("}\n")

	# boilerplate at end of file
	def close(self):
		data = """cameras
{
	"activecamera" "-1"
}
cordons
{
	"active" "0"
}
"""
		self.f.write(data)
		self.f.close()

	def fog_controller(self,z,y,x):
		data = """entity
{
	"id" "%d"
	"classname" "env_fog_controller"
	"angles" "0 0 0"
	"farz" "2200"
	"fogblend" "0"
	"fogcolor" "35 43 50"
	"fogcolor2" "255 255 255"
	"fogdir" "1 0 0"
	"fogenable" "1"
	"fogend" "2200"
	"foglerptime" "5"
	"fogmaxdensity" "1"
	"fogstart" "0"
	"HDRColorScale" "1"
	"heightFogDensity" "0.0"
	"heightFogMaxDensity" "1.0"
	"heightFogStart" "0.0"
	"maxcpulevel" "0"
	"maxdxlevel" "0"
	"maxgpulevel" "0"
	"mincpulevel" "0"
	"mindxlevel" "0"
	"mingpulevel" "0"
	"spawnflags" "1"
	"targetname" "AutoInstance1-fog_master"
	"use_angles" "0"
	"origin" "%d %d %d"
}
"""
		self.f.write(data % (self.num,x,y,z))
		self.num += 1

	def light_environment(self,z,y,x):
		data = """entity
{
	"id" "%d"
	"classname" "light_environment"
	"_ambient" "220 220 240 20"
	"_ambientHDR" "220 220 240 20"
	"_AmbientScaleHDR" "0.7"
	"_light" "255 210 220 100"
	"_lightHDR" "255 210 220 100"
	"_lightscaleHDR" "0.7"
	"angles" "-60 236 0"
	"pitch" "-19"
	"SunSpreadAngle" "5"
	"origin" "%d %d %d"
}
"""
		self.f.write(data % (self.num,x,y,z))
		self.num += 1

	def info_survivor_position(self,z,y,x):
		data = """entity
{
	"id" "%d"
	"classname" "info_survivor_position"
	"angles" "0 0 0"
	"Order" "1"
	"origin" "%d %d %d"
}
"""
		self.f.write(data % (self.num,x,y,z))
		self.num += 1

	def info_player_start(self,z,y,x):
		data = """entity
{
	"id" "%d"
	"classname" "info_player_start"
	"angles" "0 0 0"
	"Order" "1"
	"origin" "%d %d %d"
}
"""
		self.f.write(data % (self.num,x,y,z))
		self.num += 1

	def func_detail(self):
		data = """entity
{
	"id" "%d"
	"classname" "func_detail"
"""
		self.f.write(data % self.num)
		self.num += 1

# vim: ts=8 sw=8 noet
