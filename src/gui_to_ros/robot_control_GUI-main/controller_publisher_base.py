
from abc import ABC, abstractmethod

class ControllerPublisherBase(ABC):
    
    @abstractmethod
    def window_rotation_callback(self, coordinates):
        pass
    
    @abstractmethod
    def window_translation_callback(self, coordinates):
        pass
    
    @abstractmethod
    def button_rotation_callback(self, direction):
        pass

    @abstractmethod
    def button_translation_callback(self, direction):
        pass
  
    @abstractmethod
    def send_message(self):
        """Actually sends our messsage out to the """
        pass
