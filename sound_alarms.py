#!/usr/bin/env python2

#import pyparsing
import re

inp_1 = open("out_A1").readlines()
inp_2 = open("out_A2").readlines()

class hole:
  hole_birth_txg = -1
  block_type = ""
  hole_start = -1
  hole_size = -1
  def __init__(self,h_s,b_t,h_sz,hb_txg):
    self.hole_birth_txg = hb_txg
    self.hole_start = h_s
    self.block_type = b_t
    self.hole_size = h_sz
  
  def __eq__(self, other):
    return (self.hole_birth_txg == other.hole_birth_txg and \
            self.hole_start == other.hole_start and \
            self.block_type == other.block_type and \
            self.hole_size == other.hole_size)

  def __str__(self):
    return "<%s %s HOLE size=%dL birth=%dL>" % (self.hole_start,self.block_type,self.hole_size,self.hole_birth_txg)
  
  def __repr__(self):
    return str(self)
  
class state_data:
  path = ""
  snapshot = ""
  snap_txg = -1
  nonzero_holes = []
  zero_holes = []
  def __init__(self,p,sn_name,sn_txg):
    self.path = p
    self.snapshot = sn_name
    self.snap_txg = sn_txg
    self.nonzero_holes = []
    self.zero_holes = []

class test_file:
  dataset = ""
  path = ""
  inode = -1
  cr_txg = -1
  snapshot_states = {}
  def __init__(self,ds_name,p,obj,cr):
    self.dataset = ds_name
    self.path = p
    self.inode = obj
    self.cr_txg = cr
    self.snapshot_states = {}

filelist = {}

def parse_fileobj(zdbout):
  cur_fi = None
  ds_re = re.compile("Dataset (?P<dataset>([^/@]+)(/[^/@]+)*)@(?P<snapname>[^/@]+) \[ZPL\].+cr_txg (?P<cr_txg>\d+)")
  path_re = re.compile("\s+path\s+(?P<path>.+)")
  birth_re = re.compile("\s+gen\s+(?P<birth_txg>\d+)")
  obj_re = re.compile("\s+(?P<obj_id>\d+).+ ZFS plain file[^\]]")
  hole_re = re.compile("\s+(?P<hole_start>\d+)\s+(?P<block_type>L[0-9]+)\s+HOLE.*size=(?P<size>\d+)L birth=(?P<hole_birth_txg>\d+)L")
  ds = ""
  snapname = ""
  path = ""
  obj_id = -1
  zero_holes = []
  nonzero_holes = []
  parse = None
  for line in zdbout:
    if ds_re.match(line):
      parse = ds_re.match(line)
      cur_fi = None
      ds = parse.group("dataset")
      snapname = parse.group("snapname")
      snap_txg = int(parse.group("cr_txg"))
#      print ds
#      print snapname
    elif obj_re.match(line):
      parse = obj_re.match(line)
      obj_id = parse.group("obj_id")
#      print obj_id
    elif path_re.match(line):
      parse = path_re.match(line)
      path = parse.group("path")
#      print path
    elif birth_re.match(line):
      parse = birth_re.match(line)
      birth_txg = int(parse.group("birth_txg"))
#      print birth_txg
      # FIXME: at this point, we should either make a new obj or grab an existing one
      if (obj_id,birth_txg) in filelist.keys():
        cur_fi = filelist[(obj_id,birth_txg)]
      else:
        cur_fi = test_file(ds,path,obj_id,birth_txg)
        filelist[(obj_id,birth_txg)] = cur_fi
      if (snap_txg in cur_fi.snapshot_states.keys()):
        raise Error
      cur_state = state_data(path,snapname,snap_txg)
      cur_fi.snapshot_states[snap_txg] = cur_state
    elif hole_re.match(line):
      parse = hole_re.match(line)
      hole_start = parse.group("hole_start")
      block_type = parse.group("block_type")
      hole_size = int(parse.group("size"))
      hole_birth_txg = int(parse.group("hole_birth_txg"))
      newhole = hole(hole_start,block_type,hole_size,hole_birth_txg)
      if (hole_birth_txg != 0):
        cur_state.nonzero_holes.append(newhole)
      else:
        cur_state.zero_holes.append(newhole)
    
#  for k in filelist.keys():
#    print filelist[k].snapshot_states
      
      
      
        

def detect_bug(fi):
  snaplist = fi.snapshot_states.keys()
  snaps = len(snaplist)
  i = snaps
  buggy_holes = 0
#  print "i: %d" % i
  while (i > 1):
    new_snap = fi.snapshot_states[snaplist[i-1]]
    old_snap = fi.snapshot_states[snaplist[i-2]]
#    print new_snap.nonzero_holes
    for zero_hole in new_snap.zero_holes:
#      print zero_hole
      if not zero_hole in old_snap.zero_holes:
        print "Zero hole %s in snapshot %d but not %d" % (zero_hole.hole_start,new_snap.snap_txg,old_snap.snap_txg)
        buggy_holes += 1
    i -= 1 
  return (buggy_holes > 0)

parse_fileobj(inp_1)
parse_fileobj(inp_2)

for k in filelist.keys():
  fi = filelist[k]
  res = detect_bug(fi)
  if (res):
    print "hole_birth bug detected in %s" % (fi.dataset + "/" + fi.path)
