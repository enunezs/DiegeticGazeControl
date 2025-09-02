import numpy as np
from typing import List, Tuple, Collection
import yaml
from collections import namedtuple


k_values = namedtuple("k_values", ["kp", "ki", "kd"])

class CircularBuffer:
    # A simple circular buffer that stores the last n vectors provided to it.
    def __init__(self, 
                 buffer_shape: Collection) -> None:
        
        self.buffer = np.zeros(buffer_shape, dtype = np.int32)
        self.buffer_shape = buffer_shape

    def append(self, array_to_append) -> None:
        # roll the buffer by one IE input = [[0, 1, 0], [1, 0, 0]], output = [[1, 0, 0], [0, 1, 0]]
        self.buffer = np.roll(self.buffer, -1, axis=0)
        self.buffer[0] = array_to_append


class PID(CircularBuffer):
    def __init__(self, 
                 buffer_shape: Collection,
                 linear_k_values: Collection,
                 angular_k_values: Collection) -> None:

        super().__init__(buffer_shape)

        if (isinstance(angular_k_values, Collection) and not isinstance(angular_k_values, k_values)):
            self.angular_k_values = k_values(*angular_k_values)
    
        if isinstance(linear_k_values, Collection):
            self.linear_k_values = k_values(*linear_k_values)

    def diff_error(self) -> np.array:
        return self.buffer[0] - self.buffer[1]

    def int_error(self) -> np.array:
        return np.sum(self.buffer, axis=0)
    
    def error(self, target: np.array, current: np.array) -> np.array:

        error = target - current
        self.append(error)
        return error
        # Takes a new imput then returns an output.
        
    def update(self, input: np.array, target: np.array) -> np.array:
        error = self.error(target, input)
        integral = self.int_error()
        differential = self.diff_error()

        angular_update = self.angular_k_values.kp * error[3:6]

        linear_update = self.linear_k_values.kp * error[0:3]

        update = np.concatenate((linear_update, angular_update))
        print("update")
        print(update)
        return update

if __name__ == "__main__":
    pass
    target = np.array([[1,1,1,1,1,1], [1,1,1,1,1,1], [1,1,1,1,1,1],])
    
    linear_k_values = (1, 0, 0)
    angular_k_values = (1, 0, 0)

    current = np.array([0,0,0,0,0,0])
    pid = PID((3, 6), linear_k_values, angular_k_values)
    
    print(pid.buffer)
    
    for input in target:
        current = pid.update(input, current)
        print(f"current: {current}")
        
        print(f"error {pid.buffer[0]}")
        print(f"diff  {pid.diff_error()}")

        print("integral")
        print(pid.int_error())