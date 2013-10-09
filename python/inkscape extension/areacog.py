#!/usr/bin/env python 
'''
Copyright (C) 2013 Al Grant, al@algrant.ca

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

# This directory contains the inkscape specific modules
sys.path.append('/usr/share/inkscape/extensions')

import math, inkex, simplestyle, simplepath, bezmisc
from cubicsuperpath import CubicSuperPath as csp

class AreaCoG(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-a", "--angle",
                        action="store", type="float", 
                        dest="angle", default=45.0,
                        help="direction of the motion vector")
        self.OptionParser.add_option("-m", "--magnitude",
                        action="store", type="float", 
                        dest="magnitude", default=100.0,
                        help="magnitude of the motion vector")    

    def linearArea(self, x0, y0, x1, y1):
        return 0.5*(x0*y1-y0*x1)

    def linearLamina(self, u0, v0, u1, v1):
        return (u0*u0 + u1*u0 + u1*u1)*(v1 - v0)/6.0
    
    def quadraticArea(self, x0, y0, x1, y1, x2, y2):
        return (- 2*x1*y0 -x2*y0 + 2*x0 *y1 - 2*x2*y1 + x0*y2 + 2*x1*y2) / 6.0

    def quadraticLamina(self, u0, v0, u1, v1, u2, v2):
        #Generated using Mathematica
        return (1/30.0)*(u0*u0*(-5*v0 + 4*v1 + v2) + u0*(u2*(v2 - v0) + 2*u1*(-2*v0 + v1 + v2)) 
                        -2*u1*u1*(v0 - v2) - 2*u1*u2*(v0 + v1 - 2*v2) 
                        -u2*u2*(v0 + 4*v1 - 5*v2))

    def cubicArea(self, x0, y0, x1, y1, x2, y2, x3, y3):
        return (          - 6*x1*y0 - 3*x2*y0 -   x3*y0  
                + 6*x0*y1           - 3*x2*y1 - 3*x3*y1  
                + 3*x0*y2 + 3*x1*y2           - 6*x3*y2
                +   x0*y3 + 3*x1*y3 + 6*x2*y3           )/20.0

    def cubicLamina(self, u0, v0, u1, v1, u2, v2, u3, v3):
        #Generated using Mathematica
        return (1/840.0)*(5*u0**2*(-(28*v0) + 21*v1 + 6*v2 + v3) + u0* (15*u1*(-(7*v0) + 
                3*(v1 + v2) + v3) + 6*u2*(-(5*v0) + 3*v2 + 2*v3) + u3*(-(5*v0) - 3*v1 + 
                3*v2 + 5*v3)) - 18*u2**2*v0 - 5*u3**2*v0 -  15*u2*u3*v0 - 27*u2**2*v1 -  
                30*u3**2*v1 - 45*u2*u3*v1 - 105*u3**2*v2 - 45*u2*u3*v2 +  5*(9*u2**2 + 
                21*u3*u2 + 28*u3**2)*v3 + 9*u1**2*(-(5*v0) + 3*v2 + 2*v3) - 
                3*u1*(2*u3*(2*v0 + 3*v1 - 5*v3) + 3*u2*(5*v0 + 3*v1 - 3*v2 - 5*v3)))

    def effect(self):
        self.vx = math.cos(math.radians(self.options.angle))*self.options.magnitude
        self.vy = math.sin(math.radians(self.options.angle))*self.options.magnitude

        closed_paths = []
        for id, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path','svg'):

                group = inkex.etree.SubElement(node.getparent(),inkex.addNS('g','svg'))

                circle = inkex.etree.SubElement(group,inkex.addNS('path','svg'))
                circle.set('style', node.get('style'))
                crosshairX = inkex.etree.SubElement(group,inkex.addNS('path','svg'))
                crosshairY = inkex.etree.SubElement(group,inkex.addNS('path','svg'))
                
                p = simplepath.parsePath(node.get('d'))

                mass = 0
                lamina_x = 0
                lamina_y = 0

                startX, startY = p[0][1][0],p[0][1][1]
                for cmd,params in p:

                    #new.text += " %s %s"%(str(cmd),str(params))

                    if cmd == 'L':
                        x1,y1 = params[0],params[1]
                        mass += self.linearArea(x0, y0, x1, y1)
                        lamina_x += self.linearLamina(x0, y0, x1, y1)
                        lamina_y -= self.linearLamina(y0, x0, y1, x1)
                        x0,y0 = x1,y1

                    if cmd == 'C':
                        x1,y1 = params[0],params[1]
                        x2,y2 = params[2],params[3]
                        x3,y3 = params[4],params[5]
                        mass += self.cubicArea(x0,y0,x1,y1,x2,y2,x3,y3)
                        lamina_x += self.cubicLamina(x0, y0, x1, y1, x2, y2, x3, y3)
                        lamina_y -= self.cubicLamina(y0, x0, y1, x1, y2, x2, y3, x3)
                        x0,y0 = x3,y3
                    
                    if cmd == 'M':
                        x0,y0 = params[0],params[1]
                        xStart, yStart = x0,y0

                    if cmd == 'Z':
                        mass += self.linearArea(x0, y0, xStart, yStart)
                        lamina_x += self.linearLamina(x0, y0, xStart, yStart)
                        lamina_y -= self.linearLamina(y0, x0, yStart, xStart)

                if (mass < 0):
                    #path is going counter-clockwise, numbers are inverted, 
                    #will be an issue once we add objects together
                    mass = -mass
                    lamina_x = -lamina_x
                    lamina_y = -lamina_y

                size = 10
                closed_paths.append([node, mass, lamina_x,lamina_y])
                crosshairX.set('d', simplepath.formatPath([['M',[lamina_x/mass,lamina_y/mass-size]],['L',[lamina_x/mass,lamina_y/mass+size]]])) 
                crosshairX.set('style', 'stroke:#FF0000;stroke-width:1.0px;')
                crosshairY.set('d', simplepath.formatPath([['M',[lamina_x/mass-size,lamina_y/mass]],['L',[lamina_x/mass+size,lamina_y/mass]]])) 
                crosshairY.set('style', 'stroke:#FF0000;stroke-width:1.0px;')
                circle.set('d', simplepath.formatPath([ ['M',[lamina_x/mass-size/2,lamina_y/mass]],
                                                        ['L',[lamina_x/mass,lamina_y/mass-size/2]],
                                                        ['L',[lamina_x/mass+size/2,lamina_y/mass]],
                                                        ['L',[lamina_x/mass,lamina_y/mass+size/2]],
                                                        ['Z',[]]
                                                        ]))

        tot_mass, tot_lamx, tot_lamy = 0,0,0
        if len(closed_paths) > 1:
            for node,mass,lamina_x,lamina_y in closed_paths:
                tot_mass += mass
                tot_lamx += lamina_x
                tot_lamy += lamina_y

            crossHair = inkex.etree.SubElement(closed_paths[0][0].getparent().getparent(),inkex.addNS('g','svg'))
            crosshairX = inkex.etree.SubElement(crossHair,inkex.addNS('path','svg'))
            crosshairY = inkex.etree.SubElement(crossHair,inkex.addNS('path','svg'))
            crosshairX.set('d', simplepath.formatPath([['M',[tot_lamx/tot_mass,tot_lamy/tot_mass-10]],['L',[tot_lamx/tot_mass,tot_lamy/tot_mass+10]]])) 
            crosshairX.set('style', 'stroke:#FF0000;stroke-width:1.0px;')
            crosshairY.set('d', simplepath.formatPath([['M',[tot_lamx/tot_mass-10,tot_lamy/tot_mass]],['L',[tot_lamx/tot_mass+10,tot_lamy/tot_mass]]])) 
            crosshairY.set('style', 'stroke:#FF0000;stroke-width:1.0px;')


if __name__ == '__main__':
    e = AreaCoG()
    e.affect()


# vim: expandtab shiftwidth=4 tabstop=8 softtabstop=4 encoding=utf-8 textwidth=99
