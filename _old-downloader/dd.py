# legacy code i (kieu) used to download dynmaps on different ocasions. a trashy hack
# run cmd and do "dd.py <folder name> <zoom>" - if it times out just retry - rarely it will download empty tiles that are 143 bytes or skip (this can be seen by glitches in an ImageMagick render)
# yes, download area and dynmap url is to be hardcoded every time
# you need "pip install requests"

import os
import requests
import sys
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

dl_folder = sys.argv[1]
zoom = int(sys.argv[2])

base_link = 'http://server.xyz:2086/tiles/world/flat/' # http://server.xyz:2138/tiles/world/flat/{0}_{1}/{2}{3}_{4}.png // .format( X//multi, Y//multi, prefix, X, Y )
dl_full_path = os.path.join(os.getcwd(), dl_folder, str(zoom))

# range currently selected with a specialized tool called Inspect Element on a dynmap while at max zoom
# y_ = ingame Z coords inverted
# corners
# NW = lowest X, highest Y
# SE = highest X, lowest Y

x_from = 0
x_to = 0
y_from = 0
y_to = 0

multi = 32 # const - look: base_link
# forstep - on every zoom, neighboring tiles skip this much X,Y - used so no empty tile download links are generated in generate_tile_list()

zooms = [           # zoom	b/px	b/tile	prefix	forstep
(64, 'zzzzzz_'  ),  #   0	16		2048	zzzzzz_	64
(32, 'zzzzz_'   ),  #   1	8		1024	zzzzz_	32
(16, 'zzzz_'    ),  #   2	4		512		zzzz_	16
(8,  'zzz_'     ),  #   3	2		256		zzz_	8
(4,  'zz_'      ),  #   4	1		128		zz_		4
(2,  'z_'       ),  #   5	1/2		64		z_		2
(1,  ''         )]  #   6	1/4		32		-		1



def generate_tile_list(x_from, x_to, y_from, y_to, zoom): # returns a list of tuples containing x,y of every tile at given zoom

  z = zooms[zoom][0]
  tile_list = []
  
  def gen_y(x): # generate all Y tiles in a given X row, appends directly to tile_list
      
    for y in range(y_from, y_to+1): # iterate over all Y
      if y % z == 0:
        tile_list.append((x,y))
    
    if y_to % z: # this is if the topmost tile doesn't catch on with current forstep - without this, it's missing
      y = y_to
      while y % z:
        y += 1
      else:
        tile_list.append((x,y))

  if x_from % z:
    x = x_from
    while x % z:
      x -= 1
    else:
      gen_y(x)
  
  for x in range(x_from, x_to+1):
    if x % z == 0:
      gen_y(x)
  return tile_list



def download_tile(tile): # downloads a given tile at given zoom
    x = tile[0]
    y = tile[1]

    filepath = os.path.join(dl_full_path, str(tile[0]) + '_' + str(tile[1]) + '.png')

    if not os.path.isfile(filepath): # if file doesn't exist, download
      download_link = base_link + '{0}_{1}/{2}{3}_{4}.png'.format(x//multi, y//multi, zooms[zoom][1], x, y)
      print(download_link)
      
      c = 0
      while c >= 0:
        
        if c >= 10:
          print('Download failed for ' + filepath)
          break
        
        tile_download = requests.get(download_link, timeout=120000)
        open(filepath, 'wb').write(tile_download.content)
        if not os.path.isfile(filepath):
          c += 1
          print('File missing, retry attempt ' + str(c))
        elif os.stat(filepath).st_size == 143:
          #os.remove(filepath)
          c += 1
          print('Error 143, retry attempt ' + str(c))
          #print('Error 143, but keeping the file :D')
        else:
          c = -1



def generate_magick_command(x_from, x_to, y_from, y_to, zoom): # generates a command that compiles all tiles into a big .png, run from the folder with tiles - needs ImageMagick added to PATH or in the same folder - .bat will freeze if out of memory

  if os.path.isfile(os.path.join(dl_full_path, 'generated-command.bat')):
    os.remove(os.path.join(dl_full_path, 'generated-command.bat'))

  z = zooms[zoom][0]
  f = open(os.path.join(dl_full_path, 'generated-command.bat'), 'a')
  
  def gen_y(x): # generate all Y tiles in a given X row
  
    f.write('magick convert -append')
    if y_to % z: # this is if the topmost tile doesn't catch on with current forstep - without this, it's missing
      y = y_to
      while y % z:
        y += 1
      else:
        f.write(' {0}_{1}.png'.format(x,y))
    for y in range(y_to, y_from-1, -1): # iterate over all Y
      if y % z == 0:
        #f.write(' ' + x + '_' + y + '.png')
        f.write(' {0}_{1}.png'.format(x,y))
    f.write(' _{0}.png\n'.format(x))

  if x_from % z:
    x = x_from
    while x % z:
      x -= 1
    else:
      gen_y(x)
  for x in range(x_from, x_to+1):
    if x % z == 0:
      gen_y(x)
  
  
  f.write("magick convert +append") # start compiling ready_ files
  if x_from % z:
    x = x_from
    while x % z:
      x -= 1
    else:
      f.write(' x_{0}.png'.format(x))
  for x in range(x_from, x_to+1):
    if x % z == 0:
      f.write(' _{0}.png'.format(x))
      
  
  f.write(' __{0}_full.png'.format(zoom))
  f.close()
  print('Command should be generated, check your files.')


def main():
  print('Running main()...')
  
  print('- Download mode')
  # generate full tile list for given zoom
  full_tile_list = generate_tile_list(x_from,x_to,y_from,y_to,zoom)
  print('Got full_tile_list containing ' + str(len(full_tile_list)) + ' items at zoom level ' + str(zoom))
  
  
  # print exaple tile coords
  print('Printing example items...')
  #print(full_tile_list)
  #for e in range(1000): print(full_tile_list[e])
  print(full_tile_list[0])
  print(full_tile_list[1])
  print(full_tile_list[2])
  print(full_tile_list[3])
  print(full_tile_list[len(full_tile_list)//3])
  print(full_tile_list[len(full_tile_list)//2])
  print(full_tile_list[-len(full_tile_list)//3])
  print(full_tile_list[-4])
  print(full_tile_list[-3])
  print(full_tile_list[-2])
  print(full_tile_list[-1])
  print('Example print complete.')
  
  # create folders
  print('Creating folder: ' + dl_full_path)
  if not os.path.isdir(dl_full_path):
      os.makedirs(dl_full_path)
  print('Folder created or exists already.')
  
  print('Beginning download loop...')
  '''
  for tile in full_tile_list:
      download_tile(tile)
  '''
  pool = ThreadPool(8)
  pool.map(download_tile, full_tile_list)
  print('Download loop finished. Check your files. Total should be: ' + str(len(full_tile_list)))
  
  print('Generating a batch file for compiling tiles into a big .png...')
  generate_magick_command(x_from,x_to,y_from,y_to,zoom)
  
  print('Exiting main()...')