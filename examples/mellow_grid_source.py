# MELLOW: native-grid recreation, not tracing on a 268x360 canvas.
# Each character below is ONE sprite pixel.
# Grid: 41 columns x 55 rows. No reference image needed to rerender.
from PIL import Image
from pathlib import Path
WIDTH, HEIGHT = 41, 55
PALETTE = {'W': (255, 255, 255, 255),
 'R': (172, 49, 50, 255),
 'B': (92, 109, 227, 255),
 'K': (0, 0, 0, 255),
 'P': (62, 63, 115, 255),
 'r': (252, 35, 36, 255),
 'G': (212, 212, 212, 255),
 'S': (156, 173, 183, 255),
 'g': (196, 195, 198, 255),
 'D': (132, 39, 38, 255),
 'C': (96, 204, 227, 255),
 'd': (133, 22, 20, 255),
 'O': (101, 17, 14, 255),
 '.': (0, 0, 0, 0)}
PIXELS = (
    '............................rrrr.........',
    '..........................RRRRRrrrr......',
    '........................RRRRRRRRRRRrrr...',
    '...........rrrrrrr....RRRRRRRRRRRRRRRrr..',
    '.........RrrrrrrrrrRRRRRRRRRRRRRRRRRRRRr.',
    '.......RRrrrrrrrrRRRRRRRRRRRRRRRRRRRRRRrr',
    '......RRRrrrrRRRRRRRRRRRRRRRRRRRRRRRRRRRr',
    '.....RRRRrrrRRRRRRRRRRRRRRRRRRRRRRRRRRRr.',
    '.....RRRRRRRRRRRRRRgggRRRRRRRRRRRRRRRRR..',
    '....RRRRRRRRRRRRRggggggRRRRRRRRRRRRRR....',
    '....RRRRRRRRRRRWWWWWWWgGRRRRRRRRRRR......',
    '....RRRRRRRRWWWWWWWWWWWWWRRRRRRRR........',
    '....RRRRRRWWWWWWWWWWWWWWWWRRRRR..........',
    '....RRRRWWWWWWWWWWWWWWWWWWWRR............',
    '....RRgWWWWWWWWWWWWWWWWWWWWW.............',
    '....RgWWWWWWWWWWWWWWWWWWWWWW.............',
    '....RWWWWWWWWWWWWWWWWWWWWWWW.............',
    '....RWWWWWWWCCKKWWWWWCKKKWWWW............',
    '....RWWWWWCCCKKKKKWWCKKKKKWWW............',
    '.....WWWWWCCKKKKSKWCKKKKSKWWW............',
    '.....WWWWWCCKKKKKKKCKKKKKKKWW............',
    '.....WWWWWCCKKKKKKKCKKKKKKKWW............',
    '.....WWWWWCCKKKKKKKCKKKKKKKW.............',
    '.....WWWWWCCKKKKKKWCKKKKKKWW.............',
    '......WWWWWCCKKKKWWWCKKKKWWW.............',
    '......WWWWWWWWWWWWWWWWWWWWW..............',
    '.......WWWWWWWWWWWWWWWWWWW...............',
    '.......PWWWWWWWWWWWWWWWWWW...............',
    '......PPPWWWWWWWWWWWWWWW.................',
    '.....PPPPSWWWWWWWWWWWWW..................',
    '....PPPPBSSSWWWWWWWWW....................',
    '...PPPPBBBSSSSSSSBBB.....................',
    '...PPPBBBBSSSSSSSBBBB....................',
    '...PPPBBBBBSSSSSBBBBB....................',
    '...PPBBBBBBBBPBBBBBBBB...................',
    '...PPBBBBBBBBBBBBBBBBB...................',
    '...PPBBBBBBBBBPBBBBBBB...................',
    '...PPBBBBBBBBBPBPPBBBBB..................',
    '...PPBBBBBBBBBPBBPBBBBB..................',
    '...PPBBBBBBBBBBBBBBBBBB..................',
    '...PPBBBBBBBBBBBBBPBBBB..................',
    '...PPBBBBBBBBBBBBPPBBBBGG................',
    '..WWWBBBBBBBBBBBBBBBBBBGGGG..............',
    'WWWWWWWBBBBBBBBBBBBBBBBGGGG..............',
    'WWWWWWWWSBBBBBBBBPPBBBBGGGGG.............',
    'WWWWWWWWWSBBBBBBBBPBBBBGGGGG.............',
    'WWWWWWWWWWSBBBBBBBBBBBBGGGGG.............',
    'WWWWWWWSWWSBBBBBBBBBBPGGGSGG.............',
    'WSWWWWWWPPPPPPPPPPPPGGSGGSG..............',
    'WSWWSWWWR.......DDDGGSGGSGG..............',
    '.WSWWSWWWWRRWWOODgggDDgg.................',
    '...ddRWRRRWRRRODgDDDgDDD.................',
    '...dRRRRRRRRRRRDDDDDDDDDD................',
    '...dddddddddddddOOOOOOOOOO...............',
    '...WWWWWWWWWWWWWgggggggggg...............',
)
def render():
    assert len(PIXELS)==HEIGHT and all(len(r)==WIDTH for r in PIXELS)
    image=Image.new('RGBA',(WIDTH,HEIGHT))
    for y,line in enumerate(PIXELS):
        for x,key in enumerate(line):
            image.putpixel((x,y),PALETTE[key])
    return image
if __name__=='__main__':
    sprite=render()
    sprite.save('mellow_native_41x55.png')
    sprite.resize((WIDTH*10,HEIGHT*10),Image.Resampling.NEAREST).save('mellow_10x.png')
