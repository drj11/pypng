'''
Created on 05.09.2013

@author: scond_000
'''
import tempfile
import os

old = open('png.py')
temp = tempfile.TemporaryFile('w+')

temp.writelines(old)
temp.seek(0)
old.close()
os.remove('png.py')
new = open('png.py', 'w')

go = True
#All before embdeded filters
for line in temp:
    if go:
        new.write(line)
    if line.strip().startswith('#===Super-safe pngfilters'):
        go = False
    if line.strip().startswith('#/===Super-safe pngfilters'):
        break

#Embeding filters
new.write('    class pngfilters:' + '\n')
filt = open('pngfilters.py')
pre_blank = False
for line in filt:
    if line.startswith('def'):
        new.write('        @staticmethod' + '\n')
    else:
        #Here go replacements when functions in pngfilters
        #reference to functions in pngfilters
        #As the will be availible in png.py only as methods
        line = line.replace('_paeth', 'pngfilters._paeth')
    if line.strip() == '':
        # Better PEP-8 (1 blank line between methods,
        # no spaces betweeen in blank lines)
        if not pre_blank:
            new.write('\n')
        pre_blank = True
    else:
        pre_blank = False
        new.write('        ')
        new.write(line)

# Rest of png.py
new.write('    #/===Super-safe pngfilters' + '\n')
new.writelines(temp)
temp.close()
new.close()
