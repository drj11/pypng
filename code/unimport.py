'''
Created on 08.10.2013

@author: scond_000
'''
import os

src = open('png.py')
try:
    os.remove('pngfilters.py')
except:
    pass
new = open('pngfilters.py', 'w')

#Fixed part
#Cython directives
new.write('#cython: boundscheck=False\n')
new.write('#cython: wraparound=False\n')
#global const

go = False
for line in src:
    if line.startswith('class') and\
        (line.startswith('class BaseFilter')):
        go = True
    elif not (line.startswith('   ') or line.strip() == ''):
        go = False
    if go:
        new.write(line)
new.close()
