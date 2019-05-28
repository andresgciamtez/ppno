# -*- coding: utf-8 -*-
"""
*** READ AND WRITE FROM/TO []-HEADED TXT FILES ***
Andrés García Martínez (agarciam@citop.es)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
class Htxtf(object):
    """Read and write sections of headed txt files"""
    def __init__(self, fname):
        self.file = open(fname, 'r')
        
    def __del__(self):
        self.file.close()
    
    def read_section(self, secname):
        """Read a section of name secname [secname] from a file.
        return a list of cleaned strings: remove duplicate spaces and coments
        preceded by ;
        """
        cnt = 0
        section = []
        target = False
        for line in self.file:
            cnt += 1
            txt = line[0:line.find(';')]
            if target:
                if ('[' in txt):
                    break
                else:
                    if len(txt) > 0:
                        txt = tuple( c.strip() for c in txt.split())
                        section.append(txt)    
            if not(target) and '['+secname+']' in txt:
                target = True
        return section
    
    def read(self):
        """Return a dictionary which keys are the section names, and the values
        the lines."""
        sections = {}
        secname = None
        for line in self.file:
            txt = line[0:line.find(';')]
            if '[' in txt:
                # CHANGE
                secname = txt[txt.find('[')+1:txt.find(']')]
                if 'END' in txt:
                    break
                else:
                    sections[secname] = []
            else:
                if len(txt) > 0:
                    sections[secname].append(txt)
        return sections
    
    def line_to_tuple(self, line):
        '''Converts a line text to a tuple'''
        return tuple( c.strip() for c in line.split())
    
    def tuple_to_line(self, tup, sep='    '):
        '''Converts a tuple to a line text. Values are separated by sep.'''
        line = ''
        for i in tup[:-1]:
            line += str(i)
            line += sep
        line += str(tup[-1])
        return line
