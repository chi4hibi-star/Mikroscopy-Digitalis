from pygame import init, display, event, QUIT, quit, time
from statemachine import Statemachine
from traceback import print_exc

class Game():
    def __init__(self):
        init()                                                                  #init pygame
        display.set_caption('Image acquisition and processing')

        self.running = True
        self.clock = time.Clock()
        self.fps = 30
        self.state_machine = Statemachine(self.change_running)                  #State machine with application turn off function as parameter
        self.state_machine.new_display()                                        #Create new display and set display mode 
        self.state_machine.switch_scene("image_acquisition")                    #Set first Scene and create it
        return

    def run(self):
        try:
            while self.running:
                events = event.get()
                if self.state_machine.current_scene:
                    self.state_machine.current_scene.handle_events(events)                          #Call the handle_events function of the current active Scene
                    self.state_machine.current_scene.update()                                       #Call the update function of the current active Scene
                    self.state_machine.display_surface.fill((0,40,0))                               #Erase the last frame
                    self.state_machine.current_scene.draw(self.state_machine.display_surface)       #Call the draw function of the current active Scene
                    display.flip()                                                                  #Show the frame
                    self.clock.tick(self.fps)                                                       #Hold set FPS (wait and calculate)
                for s_event in events:
                    if s_event.type == QUIT:
                        self.running = False
        except Exception as e:
            print(f"Error occurred: {e}")
            print_exc()
        self.cleanup()                                                      #cleanup anything that is left
        quit()                                                                  #Quit Pygame
        return
    
    def change_running(self):
        self.running = False
        return
    
    def cleanup(self):
        if self.state_machine and self.state_machine.current_scene: 
            self.state_machine.cleanup()                                    #Call the cleanup function of each existing Scene
        return

if __name__ =='__main__':
    game = Game()
    game.run()                                                              #Run the Application