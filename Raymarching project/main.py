import pygame as pg
import moderngl, glcontext
import ctypes
import sys
from math import sin, cos, pi
from array import array
from numba import jit

class App:
    def __init__(self):
        ctypes.windll.user32.SetProcessDPIAware()
        pg.init()
        pg.mouse.set_visible(False)

        self.RES = self.WIDTH, self.HEIGHT = 1920, 974
        self.screen = pg.display.set_mode(self.RES, pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
        self.display = pg.Surface(self.RES)
        self.ctx = moderngl.create_context()

        info = pg.display.Info()

        self.clock = pg.time.Clock()
        self.time = 0
        
        self.quad_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y), uv coords (x, y)
            -1.0, 1.0, 0.0, 0.0,  # topleft
            1.0, 1.0, 1.0, 0.0,   # topright
            -1.0, -1.0, 0.0, 1.0, # bottomleft
            1.0, -1.0, 1.0, 1.0,  # bottomright
        ]))

        with open('glsl/fragment_shader.txt', 'r') as frg_shd:
            fragment_shader = frg_shd.read()
        with open('glsl/vertex_shader.txt', 'r') as vrtx_shd:
            vertex_shader = vrtx_shd.read()
        self.program = self.ctx.program(vertex_shader=vertex_shader,
                                        fragment_shader=fragment_shader)
        self.render_object = self.ctx.vertex_array(self.program,
                 [(self.quad_buffer, '2f 2f', 'vert', 'texcoord')])
        
        self.camera_pos = [0, 1, -5]
        self.camera_rotation = [0, 0, 0]
        self.camera_speed = 0.1
        self.mouse_sensivity = 1

        
    def surf_to_texture(self, surf):
        # pg surface to a texture
        tex = self.ctx.texture(surf.get_size(), 4)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.swizzle = 'BGRA'
        tex.write(surf.get_view('1'))
        return tex
    
    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT or pg.key.get_pressed()[pg.K_ESCAPE]:
                pg.quit()
                sys.exit()
            if event.type == pg.VIDEORESIZE:
                self.screen = pg.display.set_mode((event.w, event.h), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)
            

    def set_uniform(self, key, value):
        try:
            self.program[key] = value
        except KeyError:
            # print(f'{key} is not used in shader')
            pass

    def use_shader(self):
        frame_tex = self.surf_to_texture(self.display)
        frame_tex.use(0)
        # uniforms--------
        self.set_uniform('tex', 0)
        self.set_uniform('time', self.time)
        self.set_uniform('resolution', self.screen.get_size())
        self.set_uniform('ro', self.camera_pos)
        self.set_uniform('CameraRotation', self.camera_rotation)
        self.set_uniform('list', [(x, x+1, x+2) for x in range(9)])
        # uniforms--------
        self.render_object.render(mode=moderngl.TRIANGLE_STRIP)
        pg.display.flip() # sqping buffers
        frame_tex.release() # cls

    def cameraMovement(self):
        key = pg.key.get_pressed()
        cos_a = cos(self.camera_rotation[0]*(pi/180))
        sin_a = sin(self.camera_rotation[0]*(pi/180))

        if key[pg.K_w]: # forward
            self.camera_pos[2] += self.camera_speed * cos_a
            self.camera_pos[0] += self.camera_speed * sin_a
        if key[pg.K_s]: # backward
            self.camera_pos[2] += -self.camera_speed * cos_a
            self.camera_pos[0] += -self.camera_speed * sin_a
        if key[pg.K_a]: # left
            self.camera_pos[2] += self.camera_speed * sin_a
            self.camera_pos[0] += -self.camera_speed * cos_a
        if key[pg.K_d]: # right
            self.camera_pos[2] += -self.camera_speed * sin_a
            self.camera_pos[0] += self.camera_speed * cos_a
        if key[pg.K_SPACE]: self.camera_pos[1] += self.camera_speed   # up
        if key[pg.K_LSHIFT]: self.camera_pos[1] -= self.camera_speed  # down
        if key[pg.K_UP]: self.camera_speed += 0.001                   # changing the camera speed
        if key[pg.K_DOWN]: self.camera_speed -= 0.001                 # changing the camera speed

    @staticmethod  # numba does not work properly in class sometimes,
                   # so I put tit outside the class
    @jit(nopython=True)  # nopython means that it will work much faster
    def cameraRotation(mouse_pos, width, height, mouse_sensivity):
        normalized_pos = [(mouse_pos[0]-width/2) / width,
                          (mouse_pos[1]-height/2) / height]
        
        return [normalized_pos[0]*360*mouse_sensivity,
                normalized_pos[1]*180*mouse_sensivity, 0]

    def draw(self):
        self.use_shader()
        #pg.draw.circle(self.display, (255, 255, 255), [self.WIDTH//2, self.HEIGHT//2], 4)

    def run(self):
        while True:
            self.clock.tick(90)
            self.time += 1
            pg.display.set_caption(f'FPS: {self.clock.get_fps()}  Speed: {self.camera_speed}')
            
            self.check_events()
            self.draw()

            self.cameraMovement()
            self.camera_rotation = self.cameraRotation(pg.mouse.get_pos(),
                                                    *self.screen.get_size(),
                                                    self.mouse_sensivity)

app = App()
app.run()
