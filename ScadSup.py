import openpyscad as ops
import numpy as np
import math
from solid import *
from solid.utils import up, down, left, right, forward, back
class Suppressor:
    #initlize with height, and radius, also layer height

    def __init__(self, height, radius, layer_height, nozzle_diameter, caliber = 9):
        self.height = height
        self.radius = radius
        self.wall_thickness = 4
        self.layer_height = layer_height
        self.nozzle_diameter = nozzle_diameter
        self.layer_count = math.ceil(self.height / self.layer_height)
        self.layer_count = int(self.layer_count)
        #now we know how many layers our print will be
        #we need to know how many indices fit in each radius so we can determine that portion of the array
        self.caliber = caliber
        self.slice_indices = radius / nozzle_diameter
        self.slice_indices = int(self.slice_indices)
        #now we make the genome equivalent to a hollow cylinder
    
        #get number of lines in wall thickness
        wall_indices = self.wall_thickness / self.nozzle_diameter
        wall_indices = int(wall_indices)
        #empty part
        hollow_slice = [0 for i in range(self.slice_indices - wall_indices)]
        #add wall
        hollow_slice += [1 for i in range(wall_indices)]
        # we will use a numpy array to make this easier
        #  
        self.genome = np.array([hollow_slice for i in range(self.layer_count)])
        #bottom is allways ones + the threading manually added , so no need to add it here
        #we do need to add the top though so we can have a cap 
        #this shouldn't add to the height, so it should modify the genome, we'll assume the cap is the same thickness as the wall
        #we'll also assume the cap is the same thickness as the wallA
        cap_indices = self.wall_thickness / self.layer_height
        cap_indices = int(cap_indices)
        #add the cap, by modifying the genome
        self.genome[self.layer_count - cap_indices:] = 1
        #that it
    def generate_scad(self):
        #each layer is a cylinder of layer height, and radius
        #we need to generate a list of cylinders, and then union them
        #we can do this by iterating through the genome
        #we will use a list to store the cylinders
        cylinders = []
        #iterate through the genome
        for i, slice in enumerate(self.genome):
            #cylinder = ops.Cylinder(h = self.layer_height, r = self.radius)
            #generate rings using the 0's and 1's in each slice of the genome and the nozzle diameter
            #1s are solid and 0s are hollow
            rings = self.make_ring(slice)
            actual_slice = cylinder(r = self.radius, h = self.layer_height)
            for r in rings:
                if r[0] == "one":
                    actual_slice += r[1]
                if r[0] == "zero":
                    actual_slice -= r[1]
            #move the slice up by the layer height * i
            actual_slice = up(self.layer_height * i)(actual_slice)
            cylinders.append(actual_slice)
        final_model = cylinders[0]
        for c in cylinders[1:]:
            final_model += c
        final_model -= cylinder(r = self.caliber / 2, h = self.height )
        return final_model
    def make_ring(self, array, sval = 0 ):
        while  sval < len(array) and array[sval] == 1 :
            sval += 1
        if(sval >= len(array)):
            return []
        i = sval 
        while array[i] == 0 and i < len(array):
            i += 1
        ones = cylinder(r = sval * self.nozzle_diameter, h = self.layer_height)
        zeros = cylinder(r = (sval + i) * self.nozzle_diameter, h = self.layer_height)
        sub_ring = zeros - ones
        return [["one", ones], ["zero",zeros]] + self.make_ring(array, i + 1)
    def generate_side_view(self):
        sc = self.generate_scad()
        #make a cube that is the radius X radius X height
        cb = cube([self.radius*2, self.radius , self.height])
        #move it to the left by radius
        cb = left(self.radius)(cb)
        #subtract it from the suppressor
        sc -= cb
        return sc 
    def generate_text_view(self, fname = None):
        #step through genome and print either # or " "
        if(fname != None):
            with(open(fname, 'w') as f):

                for a in self.genome:
                    tmp = ""
                    for i in a:
                        if(i == 1): tmp += "#"
                        else: tmp += " "
                    a = tmp
                    #reverse a string
                    tmp = tmp[::-1] + tmp
                    f.write(tmp + "\n")
                    

    def generate_baffle(self, start, end, thickness ):
        #for now baffles are conical
        # modify the genome to have a cone
        #go to start and make the first caliber + thickness / nozzle_diameter indices 1
        start_indices = (self.caliber/2 + thickness) / self.nozzle_diameter
        start_indices = int(start_indices)
        self.genome[start][:start_indices] = 1
        #now lets see what slope we need to get to the end
        #we need to go from start to end in the number of layers
        rise = end - start 
        rise *= self.layer_height
        run = self.radius  - thickness
        #run = self.radius + self.wall_thickness
        run *= self.nozzle_diameter
        slope = rise / run
        #now we need to make the slope in the form of ones in the genome
        #go layer by layer and first do the farthest right x (slope)
        # then back fill the thickness

        for x in range(start + 1, end):
            farthest_right = int(x * slope)
            self.genome[x][farthest_right] = 1
            #now back fill the thickness
            for i in range(int(thickness/self.nozzle_diameter)):
                self.genome[x][farthest_right - i] = 1

            #cur_indices = start_indices - (thickness/2) / self.nozzle_diameter
            #cur_indices = int(cur_indices)




if __name__ == "__main__":
    import viewscad
    sup = Suppressor(80, 40, 0.2, 0.4, caliber= 9.00) 
    sup.generate_baffle(2, 80,8)
    scad = sup.generate_side_view()

    print(scad_render_to_file(scad, "tst.scad"))
    sup.generate_text_view("text.output")
    #r = viewscad.Renderer(openscad_exec = "C:\\Program Files\\OpenSCAD\\openscad.exe")
    #r.render(scad, outfile='my_thing.stl')


