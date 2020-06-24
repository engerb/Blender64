#**************************************************************
#
# Converts Blender3D models to n64 F3DEX2 microcode
# Version 0.7
# Enger Bewza - 2015 
# 
# Tested under Blender v2.76b
#
# Change log / known bugs:
#   v0.2
#       - prints data to terminal only for manual entry
#       - does not support UV's (yet...)
#       - need to check if normals are inverted and if the 
#           scaler makes a difference
#
#   v0.3
#       - now exports properly formated n64 vertex data
#       - still needs UV's
#       - algorithm needs to be designed to write the polygons
#           using a 32 vertex buffer
#
#   v0.6
#       - vertex buffer algorithm finished
#       - algorithm to write polygons finished
#       - output is looking great, even on complex models but
#           there are small polygons missing occasionally possibly
#           due to reduced number accuracy
#       - still need to fully format into .h file / format
#       - still needs UV's and RGB-A section 
#
#   v0.7
#       - fixed missing polygons, caused by last vertex in vertex buffer not being
#           written due to the split being being before the last index


import bpy


def main ():
    
    # get the active object + its vertices
    Current_obj  = bpy.context.active_object
    obj_Vertices = Current_obj.data.vertices[:] 
    obj_VertCount, obj_PolyCount = len(Current_obj.data.vertices), (len(Current_obj.data.polygons) - 1)
    
    # check the model, display warnings
    Check_Model ( Current_obj, obj_Vertices, obj_VertCount, obj_PolyCount )
    
    # open a text file
    f = open('C:/Dev/N64/Shared/output.txt', 'w')
    
    # test the model to determine an offset scale
    Global_Scale = Get_Model_Offset (Current_obj, obj_Vertices)
    
    # write a list of vertices along with their UV's and normals
    Vertex_List (Current_obj, obj_Vertices, Global_Scale, f)
    
    # write a list of polygons and how they are described
    f.write('\n \n')
    Polygon_List (Current_obj, obj_PolyCount, f)
    
    # close the text file
    f.close()
    
    return
    
    
    
#**************************************************************
#  
# Function that creates a vertex list from the active object
#

def Vertex_List (Current_obj, obj_Vertices, Global_Scale, f):

    n64_Normal = {}
    UV_data = ''

    for vert in obj_Vertices:
        
        # grab the normal vector for the current vertex
        n64_Normal = Convert_To_N64_Normal (vert.normal)
        
        # write the vertex XYZ coordinates with scale offset 
        # can format better! 
        for i in range(3):
            
            if i is 0:
                f.write('   { ')
                
            f.write( "{:>4}".format( str(int(round(vert.co[i] * Global_Scale))) ) + ', ')
            
            # flag and UV placeholder
            if i is 2:
                #f.write('0, 0, 0, ')
                UV_data = Get_UVs ( Current_obj, vert )
                
                f.write('0, ' + UV_data)
        
        # write the normal vector
        for i in range(3):
            f.write( "{:>4}".format(str(n64_Normal[i])) + ', ')
        
        # end line with Alpha and curly brace
        f.write('255 }, /* ' + str(vert.index) + ' */ \n')
   
            
    return



#**************************************************************
#  
# Function that maps UV's
#

def Get_UVs ( Current_obj, vert ):
    
    none = '0, 0, '
    
    #for item in (ob.data.uv_layers.active.data[loop].uv if ob.data.uv_layers.active!=None else (0,0)):#uv
    print(vert.index, str(Current_obj.data.uv_layers.active.data[(vert.index - 1)].uv))
    #check if there are UV's, return '0, 0, ' if none
    #check if more than one, if yes, inform that we will only use the first one
     
    #check the texture attacjed to the UV's and ensure that it is the corect X - Y and bits (tag system?)
    
    #use the x and y as a range to offset the uv's up to a max of (2046?) if over, warn and clamp
    
    #potentially add to a list of textures that will need to be converted afterwards
    
    return none
    
    
    
#**************************************************************
#  
# Function that creates a list of polygons described by each 
# vertex number with an applied offset from the vertex buffer
#

def Polygon_List (Current_obj, PolyCount, f):

    vertexCache1, vertexCache2 = [], []
    vertexList = []
    
    for polygon in Current_obj.data.polygons:  
        
        verts_in_face = polygon.vertices[:] 
        
        # create a new buffer list if any of the vertexes are not in the current buffer list 
        if all(x in vertexList for x in verts_in_face) is False or (not vertexList):
            
            # write if single polygon still cached with old buffer list, then clear
            if vertexCache1:
                vertexCache1 = Write_SinglePoly ( vertexCache1, polygon1, f )
            
            vertexList = Vertex_Buffer (Current_obj, polygon.index, f)
        
        # store first polygon into a cache with vertex buffer indexes
        if not vertexCache1 and polygon.index != PolyCount:
            vertexCache1 = Store_vertexCache (vertexList, verts_in_face)
            polygon1 = polygon.index
            
            continue; 
            
        # write cached and current polygon, then clear
        if vertexCache1:
            vertexCache2 = Store_vertexCache (vertexList, verts_in_face)
            
            vertexCache1, vertexCache2 = Write_DoublePoly ( vertexCache1, 
                vertexCache2, polygon1, polygon.index, f )
        
        # write leftover single polygon if there is one, then clear
        else:
            vertexCache1 = Store_vertexCache (vertexList, verts_in_face)
            vertexCache1 = Write_SinglePoly ( vertexCache1, polygon.index, f )
               
    f.write("    gsSPEndDisplayList() \n};")
    
    return



#**************************************************************
#  
# Function that creates compares polygon vertex numbers against
# the created vertex buffer list, and returns the corect index
# to reference itself 
#

def Store_vertexCache (vertexList, verts_in_face):
    
    vertexCache = (vertexList.index(verts_in_face[0]), vertexList.index(verts_in_face[1]), 
        vertexList.index(verts_in_face[2]), 0)
    
    return vertexCache
    


#**************************************************************
#  
# Function that writes a single polygon, then returns a clear
#

def Write_SinglePoly ( vertCache1, poly1, f ):
    
    one_Vtx  = '    gsSP1Triangle('
    vtx_0    = "{:>3}".format(str(vertCache1[0])) + ', '
    vtx_1    = "{:>2}".format(str(vertCache1[1])) + ', '
    vtx_2    = "{:>2}".format(str(vertCache1[2])) + ', '
    vtx_flag = str(vertCache1[3]) + '),   /*'
    poly  = "{:>4}".format(str(poly1)) + ' */ \n'
    
    f.write(one_Vtx + vtx_0 + vtx_1 + vtx_2 + vtx_flag + poly)  
    
    return []
    


#**************************************************************
#  
# Function that writes a two polygons, then returns a clear
#

def Write_DoublePoly ( vertCache1, vertCache2, poly1, poly2, f ):
    
    two_Vtx   = '    gsSP2Triangles('
    vtx1_0    = '{:>3}'.format(str(vertCache1[0])) + ', '
    vtx1_1    = '{:>2}'.format(str(vertCache1[1])) + ', '
    vtx1_2    = '{:>2}'.format(str(vertCache1[2])) + ', '
    vtx1_flag =         str(vertCache1[3])         + ', '
    vtx2_0    = '{:>2}'.format(str(vertCache2[0])) + ', '
    vtx2_1    = '{:>2}'.format(str(vertCache2[1])) + ', '
    vtx2_2    = '{:>2}'.format(str(vertCache2[2])) + ', '
    vtx2_flag =         str(vertCache2[3])         + '),   /*'
    poly1     = '{:>4}'.format(str(poly1))         + ' '
    poly2     = '{:>4}'.format(str(poly2))         + ' */ \n'
    
    f.write(two_Vtx + vtx1_0 + vtx1_1 + vtx1_2 + vtx1_flag + 
        vtx2_0 + vtx2_1 + vtx2_2 + vtx2_flag + poly1 + poly2)  
    
    return [], []
    


#**************************************************************
#  
# Function that writes the vertex buffer
#

def Write_Buffer ( Current_obj, vtxAddress, bufferLength, bufferOffset, f ):
    
    intro   = '    gsSPVertex('
    name    = '&vtx_torus['
    address = '{:>4}'.format(str(vtxAddress))   + '], '
    length  = '{:>2}'.format(str(bufferLength)) + ', '
    offset  = '{:>2}'.format(str(bufferOffset)) + '),\n'
    
    f.write(intro + name + address + length + offset)
    
    return
    


#**************************************************************
#  
# Function that builds the vertex buffer. This works by jogging
# through the polygons and adding unique vertex numbers to a 
# list if the length is less / equal to 32. The list is then 
# ordered and iterated through to determine how to write it to
# the vertex buffer with offsets and address locations.
#
# The list is then passed back to Polygon_List() so that it 
# knows what index offsets to apply when writing polygons as
# well as to compare against  
#  


def Vertex_Buffer (Current_obj, CurrentPoly, f): 
    
    vtxAddress, bufferOffset, bufferLength = 0, 0, 0
    uniqueVertexList, vertexList           = [], []
    maxLength                              = 32
            
    # loop starting at passed polygon index
    for polygon in Current_obj.data.polygons[CurrentPoly:]: 
        
        verts_in_face = polygon.vertices[:] 
            
        # create a temporary unique vertex list
        for i in range(3):
            if (verts_in_face[i] not in vertexList):
                uniqueVertexList += [verts_in_face[i]]
            
        # dump to the main vertex list if length under 32
        if (len(vertexList) + len(uniqueVertexList)) <= maxLength:
            vertexList      += uniqueVertexList
            uniqueVertexList = []
                
                
    # sort the list ascending
    vertexList.sort()
    
    # loop through index, number in the vertex list
    for i, n in enumerate(vertexList):
        
        # store first vertex address
        if (i is 0):
            vtxAddress, bufferTotal = n, 0
            continue
            
        # jog forward until incontinuity is reached, write vertex buffer 
        if (vertexList[i] - vertexList[i - 1]) is not 1:
            bufferTotal +=  bufferLength
            bufferLength = (i - bufferTotal) 
            
            Write_Buffer (Current_obj, vtxAddress, bufferLength, bufferOffset, f)
            
            vtxAddress, bufferOffset = n, i
            
            # so we don't miss last entry if split is at end of list
            if i is not (len(vertexList) - 1):
                continue
        
        # write only or last polygon buffer    
        if i is (len(vertexList) - 1):
            bufferTotal += bufferLength
            bufferLength = (i - (bufferTotal - 1))
            
            Write_Buffer (Current_obj, vtxAddress, bufferLength, bufferOffset, f) 
        
    return vertexList



#**************************************************************
#  
# Function that converts blenders vertex normals into a 
# format the n64 can use
#

def Convert_To_N64_Normal ( Vertex_Normal ):
    
    n64_Normal = {}
    
    # blender3D normal range
    NormalMax, NormalMin = 1, -1
    NormalRange = (NormalMax - NormalMin) 

    # n64 normal range
    hex16Max, hex16Min = 127, -128
    hex16Range = (hex16Max - hex16Min)
    
    # loop through the vector and shift ranges
    for i in range(3):
        n64_Normal[i] = int(round( (((Vertex_Normal[i] - 
            NormalMin) * hex16Range) / NormalRange) + hex16Min))
    
    return n64_Normal
    
    

#**************************************************************
#  
# Function that determines the offset for maximum model scale 
# to preserve vertex coordinates accuracy 
#   

def Get_Model_Offset(Current_obj, obj_Vertices):
    
    # placeholder for bounds test
    # keep models within 2 blender units and everything should be fine
    
    return 120



#**************************************************************
#  
# Function to check if the model meets certain criteria: 
#
#   On a scale of green to red:
#        Green:     will print advice for model optimization 
#       Yellow:     will attempt to fix if possible 
#                       (example: convert quads to triangles)
#          Red:     may halt with exceptions
#  

def Check_Model ( Current_obj, obj_Vertices, obj_VertCount, obj_PolyCount ):
    
    # placeholder
    
    return


# main() and function order hack   
if __name__ == '__main__':
    main()