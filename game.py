from machine import Pin, SPI
from ili9341 import Display, color565
from xglcd_font import XglcdFont
import time
import random
import _thread

spi = SPI(1, baudrate=40000000, sck=Pin(10, Pin.OUT), mosi=Pin(11, Pin.OUT))
DISPLAY = Display(spi, dc=Pin(16), cs=Pin(18), rst=Pin(17))

GEEL = color565(243, 239, 17)
GROEN = color565(41, 223, 74)
ROZE = color565(226, 206, 160)
ROOD = color565(212, 63, 23)
BLAUW = color565(49, 222, 227)
ZWART = color565(0, 0, 0)
WIT = color565(255, 255, 255)
DONKERBLAUW = color565(12, 89, 340 )
UNISPACE = XglcdFont('font_unispace12x24.c', 12, 24)


class Banner:
    def __init__(self):
        self.text = ""
        self.x = 0
        self.y = 0

    def schrijf(self, x, y, text):
        # Vanwege foutje of feature (?) moet de tekst reversed worden om te zorgen dat het goed op het display komt.
        self.clear()
        self.text = ""
        for letter in reversed(text):
            self.text += letter
        self.x = x
        self.y = y
        DISPLAY.draw_text(self.x, self.y, self.text, UNISPACE, WIT, BLAUW, landscape=True, rotate_180=False)
        
    def clear(self):
        DISPLAY.draw_text(self.x,self.y, self.text, UNISPACE, BLAUW, BLAUW, landscape=True, rotate_180=False)
        


class Background:
    HOOGTE_GRASS = 12
    def __init__(self):
        DISPLAY.clear(BLAUW)
        self.sun()
        self.grass()
       
    def sun(self):
        DISPLAY.fill_circle(204,35,25, GEEL)

    def grass(self):
        DISPLAY.fill_rectangle(0,0,self.HOOGTE_GRASS,319, GROEN)


class Tijd:
    def __init__(self):
        self.spel_tijd()
        
    def spel_tijd(self):
        self.spel_tijd = self.spel_tijd + 1


class Paddenstoel:
    START_X = 280
    def __init__(self):
        self.x = self.START_X
        self.y = Background.HOOGTE_GRASS
        self.breedte = 32
        self.hoogte = 32
        self.show()
        
    def show(self):
        self._bovenkant()
        self._onderkant()
        
    def _clear(self):
        # x=y, y=x landscape mode
        DISPLAY.fill_rectangle(self.y, self.x, self.hoogte, self.breedte, BLAUW)
    
    def _bovenkant(self):
        hoogte_top = int(self.hoogte * 1/3)
        breedte_top = self.breedte
        x = self.y + int(self.hoogte * 2/3)
        y = self.x 
        DISPLAY.fill_rectangle(x, y, hoogte_top, breedte_top, ROOD)
         
    def _onderkant(self):
        hoogte = int(self.hoogte * 2/3)
        breedte = int(self.breedte * 1/2)
        x = self.y
        y = self.x + int(self.breedte * 1/4)
        DISPLAY.fill_rectangle(x, y, hoogte, breedte, ROZE)
    
    def move(self):
        if self.x > 0:
            self._clear()
            self.x -= 1
            self.show()
        else:
            self._clear()
            
    def top_left(self):
        return self.x, self.y + self.hoogte
    
    def top_right(self):
        return self.x + self.breedte, self.y + self.hoogte
    
    def bottom_left(self):
        return self.x, self.y

    def bottom_right(self):
        return self.x + self.breedte, self.y

    
    def has_passed_by(self):
        border = 10
        if self.x < border:
            return True
        return False
            

class Player:
    UP = "up"
    DN = "down"
    JUMP_HEIGHT = 70
    def __init__(self):
        self.x = 100
        self.y = Background.HOOGTE_GRASS
        self.hoogte = 22
        self.breedte = 6
        self.jumping = ""
        self.show(self.y)
        
    def clear(self):
        DISPLAY.fill_rectangle(self.y, self.x , self.hoogte, self.breedte, BLAUW)
    
    def show(self, nieuwe_y):
        if nieuwe_y != self.y:
            self.clear()
        self.y = nieuwe_y
        DISPLAY.fill_rectangle(self.y, self.x , self.hoogte, self.breedte, DONKERBLAUW)
        
    def move(self):
        y = self.y
        if self.jumping == self.UP:
            if y < self.JUMP_HEIGHT:
                y += 1
                self.show(nieuwe_y=y)
            else:
                self.jumping = self.DN
        if self.jumping == self.DN:
            if y > Background.HOOGTE_GRASS:
                y -= 1
                self.show(nieuwe_y=y)
            else:
                self.jumping = ""
    
    def jump(self, pin):
        self.jumping = self.UP
        
    def hit(self, xy):
        x, y = xy
        if x in range(self.x, self.x + self.breedte + 1):
            if y in range(self.y, self.y + self.hoogte + 1):
                return True
        return False
    
    def leftside(self):
        return self.x
    
    
class Game:
    def __init__(self):
        self.background = Background()
        self.paddenstoel = Paddenstoel()
        self.player = Player()
        self.banner = Banner()
        pin = Pin(15, Pin.IN, Pin.PULL_UP)
        pin.irq(trigger=Pin.IRQ_FALLING, handler=self.player.jump)

    def start(self):
        self.banner.schrijf(120, 200, "Ready")
        time.sleep(1)
        self.banner.schrijf(120, 180, "Set")
        time.sleep(1)
        self.banner.schrijf(120, 175, "Go")
        time.sleep(1)
        self.banner.schrijf(120, 150, "")
        self.play()
        
    def botsing(self):
        if  self.player.hit(self.paddenstoel.top_left()) or \
            self.player.hit(self.paddenstoel.top_right()) or \
            self.player.hit(self.paddenstoel.bottom_left()) or \
            self.player.hit(self.paddenstoel.bottom_right()):
                
            return True
        return False
        
        
    def play(self):
        while not self.botsing() and not self.paddenstoel.has_passed_by():
            self.paddenstoel.move()
            self.player.move()
            time.sleep(0.01)
        if self.paddenstoel.has_passed_by():
            self.over("Game over, you won")
        else:
            self.over("Game over, you lost")
    
    def over(self, text):
        self.banner.schrijf(120, 270, text)
        
    
game = Game()
game.start()
