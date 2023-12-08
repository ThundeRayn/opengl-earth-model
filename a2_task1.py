import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr
from OpenGL import GL as gl
import tinyobjloader

class Component:


    def __init__(self, position, eulers,up):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)

class Scene:

    def __init__(self):

        self.enemySpawnRate = 0.1

        self.face = Component(
            position = [0,100,0],
            eulers = [0, 0, 0],
            up = [0,1,0]
        )
        self.cube = Component(
            position = [0,0,0],
            eulers = [0, 0, 0],
            up = [0,1,0]
        )
    def update(self,rate):
        pass

class App:


    def __init__(self, screenWidth, screenHeight):

        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        self.renderer = GraphicsEngine()

        self.scene = Scene()

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0
        self.lightCount = 0

        self.mainLoop()

    def mainLoop(self):
        ss_id = 0 #screenshot id
        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
                            #press key p will capture screen shot
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_p:
                        print ("Capture Window ", ss_id)
                        buffer_width, buffer_height = 1024,768
                        ppm_name = "Assignment0-ss" + str(ss_id) + ".ppm"
                        self.dump_framebuffer_to_ppm(ppm_name, buffer_width, buffer_height)
                        ss_id += 1
            
            self.handleKeys()

            self.scene.update(self.frameTime * 0.05)
            
            self.renderer.render(self.scene)

            #timing
            self.calculateFramerate()
        
        self.quit()

    def handleKeys(self):

        keys = pg.key.get_pressed()

    def calculateFramerate(self):

        self.currentTime = pg.time.get_ticks()
        delta = self.currentTime - self.lastTime
        if (delta >= 1000):
            framerate = max(1,int(1000.0 * self.numFrames/delta))
            pg.display.set_caption(f"Running at {framerate} fps.")
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(1000.0 / max(1,framerate))
        self.numFrames += 1

    def dump_framebuffer_to_ppm(self,ppm_name, fb_width, fb_height):
        pixelChannel = 3
        pixels = gl.glReadPixels(0, 0, fb_width, fb_height, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        fout = open(ppm_name, "w")
        fout.write('P3\n{} {}\n255\n'.format(int(fb_width), int(fb_height)))
        for i in range(0, fb_height):
            for j in range(0, fb_width):
                cur = pixelChannel * ((fb_height - i - 1) * fb_width + j)
                fout.write('{} {} {} '.format(int(pixels[cur]), int(pixels[cur+1]), int(pixels[cur+2])))
            fout.write('\n')
        fout.flush()
        fout.close()
    
    def quit(self):
        
        self.renderer.destroy()

class GraphicsEngine:

    def __init__(self):

        self.palette={
            "COLOR": np.array([0.8,0.7,0.6],dtype = np.float32)
        }

        #initialise pygame
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((1024,768), pg.OPENGL|pg.DOUBLEBUF)

        #initialise opengl
        glClearColor(0.3, 0.4, 0.5, 1)
        glEnable(GL_DEPTH_TEST|GL_LESS)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        #glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
        glEnable (GL_CULL_FACE)

        #create renderpasses and resources
        self.faceMesh = Mesh("model/data_a2/faces/34.obj")
        #self.cubeMesh = Mesh("model/data_a2/cube.obj")
        shader = self.createShader("shaders/a2_v_try.txt", "shaders/a2_f_try.txt")
        self.renderPass = RenderPass(shader)
       
    
    def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader

    def render(self, scene):

        #refresh screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.renderPass.render(scene, self)

        pg.display.flip()

    def destroy(self):

        pg.quit()

class RenderPass:

    def __init__(self, shader):

        #initialise opengl
        self.shader = shader
        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 60, aspect = 1024/768, 
            near = 0.1, far = 1000, dtype=np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"projection"),
            1, GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.colorLoc = glGetUniformLocation(self.shader, "object_color")

    def render(self, scene, engine):

        glUseProgram(self.shader)

        view_transform = pyrr.matrix44.create_look_at(
            eye = np.array([0,100,100],dtype=np.float32),
            target = np.array(scene.face.position,dtype=np.float32),
            up = np.array(scene.face.up, dtype = np.float32),dtype=np.float32
        )
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)

        #cube
        '''glUniform3fv(self.colorLoc,1,engine.palette["COLOR"])
        modelTransform=pyrr.matrix44.create_identity(dtype=np.float32)
        glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,modelTransform)
        glBindVertexArray(engine.cubeMesh.vao)
        glDrawArrays(GL_TRIANGLES,0,engine.cubeMesh.vertex_count)'''

        #face
        glUniform3fv(self.colorLoc,1,engine.palette["COLOR"])
        modelTransform=pyrr.matrix44.create_identity(dtype=np.float32)
        glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,modelTransform)
        glBindVertexArray(engine.faceMesh.vao)
        glDrawArrays(GL_TRIANGLES,0,engine.faceMesh.vertex_count)

    def destroy(self):
        glDeleteProgram(self.shader)

class Mesh:

    def __init__(self, filename):
        # tinyobjloader
        reader = tinyobjloader.ObjReader()
        ret = reader.ParseFromFile(filename)
        attrib = reader.GetAttrib()

        # x, y, z, s, t, nx, ny, nz
        self.vertices = self.loadMesh(filename)
        self.vertex_count = len(self.vertices)//8
        self.vertices = np.array(self.vertices, dtype=np.float32)
        print(len(self.vertices)//8)#=13680

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        #normal
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))

    
    def loadMesh(self, filename):

        #raw, unassembled data
        v = []
        vt = []
        vn = []
        
        #final, assembled and packed result
        vertices = []

        #open the obj file and read the data
        with open(filename,'r') as f:
            line = f.readline()
            while line:
                firstSpace = line.find(" ")
                flag = line[0:firstSpace]
                if flag=="v":
                    #vertex
                    line = line.replace("v ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    v.append(l)
                elif flag=="vt":
                    #texture coordinate
                    line = line.replace("vt ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vt.append(l)
                elif flag=="vn":
                    #normal
                    line = line.replace("vn ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vn.append(l)
                elif flag=="f":
                    #face, three or more vertices in v/vt/vn form
                    line = line.replace("f ","")
                    line = line.replace("\n","")
                    #get the individual vertices for each line
                    line = line.split(" ")
                    faceVertices = []
                    faceTextures = []
                    faceNormals = []
                    for vertex in line:
                        #break out into [v,vt,vn],
                        #correct for 0 based indexing.
                        l = vertex.split("/")
                        position = int(l[0]) - 1
                        faceVertices.append(v[position])
                        texture = int(l[1]) - 1
                        faceTextures.append(vt[texture])
                        normal = int(l[2]) - 1
                        faceNormals.append(vn[normal])
                    # obj file uses triangle fan format for each face individually.
                    # unpack each face
                    triangles_in_face = len(line) - 2

                    vertex_order = []
                    """
                        eg. 0,1,2,3 unpacks to vertices: [0,1,2,0,2,3]
                    """
                    for i in range(triangles_in_face):
                        vertex_order.append(0)
                        vertex_order.append(i+1)
                        vertex_order.append(i+2)
                    for i in vertex_order:
                        for x in faceVertices[i]:
                            vertices.append(x)
                        for x in faceTextures[i]:
                            vertices.append(x)
                        for x in faceNormals[i]:
                            vertices.append(x)
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))
 
myApp = App(1024,768)