from threading import Thread, Lock, Event
from time import sleep
from typing import Tuple, Optional, Callable
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Stage control disabled.")

class StageController:
    """
    Controls a 3-axis stepper motor stage using A4988 drivers
    
    Coordinate system: [X, Y, Z] in mm
    - Homing moves to negative endstops and sets position to [0, 0, 0]
    - X and Y can move simultaneously
    - Z moves separately after X/Y complete
    """
    PINS = {
        'EN': {'X': 15, 'Y': 31, 'Z': 37},
        'STEP': {'X': 11, 'Y': 22, 'Z': 35},
        'DIR': {'X': 13, 'Y': 29, 'Z': 36},
        'ENDSTOP_NEG': {'X': 16, 'Y': 32, 'Z': 38},
        'ENDSTOP_POS': {'X': 18, 'Y': 33, 'Z': 40}
    }
    STEP_DELAY_US = 1
    def __init__(self, settings, on_move_complete: Optional[Callable] = None):
        """
        Initialize the stage controller
        
        Args:
            settings: Settings object with saved_settings['motors'] containing steps_per_mm
            on_move_complete: Optional callback function called when move completes
        """
        self.settings = settings
        self.on_move_complete = on_move_complete
        if not GPIO_AVAILABLE:
            self.initialized = False
            print("Stage controller not initialized: GPIO not available")
            return
        self.position = [0.0, 0.0, 0.0]
        self.position_lock = Lock()
        self.limits = {
            'X': {'min': 0.0, 'max': None},
            'Y': {'min': 0.0, 'max': None},
            'Z': {'min': 0.0, 'max': None}
        }
        self.move_thread = None
        self.is_moving = False
        self.stop_move = Event()
        try:
            self._init_gpio()
            self.initialized = True
            print("Stage controller initialized successfully")
        except Exception as e:
            self.initialized = False
            print(f"Error initializing stage controller GPIO: {e}")
        return
    
    def _init_gpio(self) -> None:
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        for axis in ['X', 'Y', 'Z']:
            GPIO.setup(self.PINS['EN'][axis], GPIO.OUT)
            GPIO.output(self.PINS['EN'][axis], GPIO.HIGH)
            GPIO.setup(self.PINS['STEP'][axis], GPIO.OUT)
            GPIO.output(self.PINS['STEP'][axis], GPIO.LOW)
            GPIO.setup(self.PINS['DIR'][axis], GPIO.OUT)
            GPIO.output(self.PINS['DIR'][axis], GPIO.LOW)
            GPIO.setup(self.PINS['ENDSTOP_NEG'][axis], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.PINS['ENDSTOP_POS'][axis], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        return
    
    def get_position(self) -> Tuple[float, float, float]:
        """
        Get current position
        
        Returns:
            Tuple of (x, y, z) in mm
        """
        with self.position_lock:
            return tuple(self.position)
    
    def move_to(self, x: Optional[float] = None, y: Optional[float] = None, 
                z: Optional[float] = None, wait: bool = False) -> bool:
        """
        Move to absolute position in mm
        
        Args:
            x: Target X position in mm (None to keep current)
            y: Target Y position in mm (None to keep current)
            z: Target Z position in mm (None to keep current)
            wait: If True, block until move completes
        
        Returns:
            True if move started successfully, False otherwise
        """
        if not self.initialized:
            print("Stage controller not initialized")
            return False
        if self.is_moving:
            print("Move already in progress")
            return False
        current_x, current_y, current_z = self.get_position()
        target_x = x if x is not None else current_x
        target_y = y if y is not None else current_y
        target_z = z if z is not None else current_z
        self.is_moving = True
        self.stop_move.clear()
        self.move_thread = Thread(target=self._execute_move, 
                                  args=(target_x, target_y, target_z),
                                  daemon=True)
        self.move_thread.start()
        if wait:
            self.move_thread.join()
        return True
    
    def _execute_move(self, target_x: float, target_y: float, target_z: float) -> None:
        """
        Execute the move (runs in separate thread)
        
        Args:
            target_x: Target X position in mm
            target_y: Target Y position in mm
            target_z: Target Z position in mm
        """
        try:
            self._move_xy(target_x, target_y)
            self._move_z(target_z)
        except Exception as e:
            print(f"Error during move: {e}")
        finally:
            self.is_moving = False
            if self.on_move_complete:
                self.on_move_complete()
        return
    
    def _move_xy(self, target_x: float, target_y: float) -> None:
        """
        Move X and Y axes simultaneously
        
        Args:
            target_x: Target X position in mm
            target_y: Target Y position in mm
        """
        current_x, current_y, _ = self.get_position()
        steps_x = self._mm_to_steps(target_x - current_x, 'X')
        steps_y = self._mm_to_steps(target_y - current_y, 'Y')
        if steps_x == 0 and steps_y == 0:
            return
        dir_x = GPIO.HIGH if steps_x > 0 else GPIO.LOW
        dir_y = GPIO.HIGH if steps_y > 0 else GPIO.LOW
        GPIO.output(self.PINS['DIR']['X'], dir_x)
        GPIO.output(self.PINS['DIR']['Y'], dir_y)
        if steps_x != 0:
            GPIO.output(self.PINS['EN']['X'], GPIO.LOW)
        if steps_y != 0:
            GPIO.output(self.PINS['EN']['Y'], GPIO.LOW)
        steps_x = abs(steps_x)
        steps_y = abs(steps_y)
        max_steps = max(steps_x, steps_y)
        for step in range(max_steps):
            if self.stop_move.is_set():
                break
            if step < steps_x:
                if not self._check_endstop('X', dir_x == GPIO.HIGH):
                    GPIO.output(self.PINS['STEP']['X'], GPIO.HIGH)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    GPIO.output(self.PINS['STEP']['X'], GPIO.LOW)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    delta = self._steps_to_mm(1 if dir_x == GPIO.HIGH else -1, 'X')
                    with self.position_lock:
                        self.position[0] += delta
            if step < steps_y:
                if not self._check_endstop('Y', dir_y == GPIO.HIGH):
                    GPIO.output(self.PINS['STEP']['Y'], GPIO.HIGH)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    GPIO.output(self.PINS['STEP']['Y'], GPIO.LOW)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    delta = self._steps_to_mm(1 if dir_y == GPIO.HIGH else -1, 'Y')
                    with self.position_lock:
                        self.position[1] += delta
        GPIO.output(self.PINS['EN']['X'], GPIO.HIGH)
        GPIO.output(self.PINS['EN']['Y'], GPIO.HIGH)
        return
    
    def _move_z(self, target_z: float) -> None:
        """
        Move Z axis
        
        Args:
            target_z: Target Z position in mm
        """
        _, _, current_z = self.get_position()
        steps = self._mm_to_steps(target_z - current_z, 'Z')
        if steps == 0:
            return
        direction = GPIO.HIGH if steps > 0 else GPIO.LOW
        GPIO.output(self.PINS['DIR']['Z'], direction)
        GPIO.output(self.PINS['EN']['Z'], GPIO.LOW)
        steps = abs(steps)
        for _ in range(steps):
            if self.stop_move.is_set():
                break
            if not self._check_endstop('Z', direction == GPIO.HIGH):
                GPIO.output(self.PINS['STEP']['Z'], GPIO.HIGH)
                sleep(self.STEP_DELAY_US / 1_000_000)
                GPIO.output(self.PINS['STEP']['Z'], GPIO.LOW)
                sleep(self.STEP_DELAY_US / 1_000_000)
                delta = self._steps_to_mm(1 if direction == GPIO.HIGH else -1, 'Z')
                with self.position_lock:
                    self.position[2] += delta
        GPIO.output(self.PINS['EN']['Z'], GPIO.HIGH)
        return
    
    def home(self, wait: bool = True) -> bool:
        """
        Home all axes to negative endstops and set position to [0, 0, 0]
        
        Args:
            wait: If True, block until homing completes
        
        Returns:
            True if homing started successfully
        """
        if not self.initialized:
            print("Stage controller not initialized")
            return False
        if self.is_moving:
            print("Move already in progress")
            return False
        self.is_moving = True
        self.stop_move.clear()
        self.move_thread = Thread(target=self._execute_home, daemon=True)
        self.move_thread.start()
        if wait:
            self.move_thread.join()
        return True
    
    def _execute_home(self) -> None:
        """Execute homing procedure (runs in separate thread)"""
        try:
            print("Homing stage...")
            self._home_xy()
            self._home_z()
            with self.position_lock:
                self.position = [0.0, 0.0, 0.0]
            print("Homing complete: Position = [0.0, 0.0, 0.0]")
        except Exception as e:
            print(f"Error during homing: {e}")
        finally:
            self.is_moving = False
            if self.on_move_complete:
                self.on_move_complete()
        return
    
    def _home_xy(self) -> None:
        """Home X and Y axes to negative endstops"""
        GPIO.output(self.PINS['DIR']['X'], GPIO.LOW)
        GPIO.output(self.PINS['DIR']['Y'], GPIO.LOW)
        GPIO.output(self.PINS['EN']['X'], GPIO.LOW)
        GPIO.output(self.PINS['EN']['Y'], GPIO.LOW)
        x_homed = False
        y_homed = False
        while not (x_homed and y_homed) and not self.stop_move.is_set():
            if not x_homed:
                if self._check_endstop('X', False):
                    x_homed = True
                else:
                    GPIO.output(self.PINS['STEP']['X'], GPIO.HIGH)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    GPIO.output(self.PINS['STEP']['X'], GPIO.LOW)
                    sleep(self.STEP_DELAY_US / 1_000_000)
            if not y_homed:
                if self._check_endstop('Y', False):
                    y_homed = True
                else:
                    GPIO.output(self.PINS['STEP']['Y'], GPIO.HIGH)
                    sleep(self.STEP_DELAY_US / 1_000_000)
                    GPIO.output(self.PINS['STEP']['Y'], GPIO.LOW)
                    sleep(self.STEP_DELAY_US / 1_000_000)
        GPIO.output(self.PINS['EN']['X'], GPIO.HIGH)
        GPIO.output(self.PINS['EN']['Y'], GPIO.HIGH)
        return
    
    def _home_z(self) -> None:
        """Home Z axis to negative endstop"""
        GPIO.output(self.PINS['DIR']['Z'], GPIO.LOW)
        GPIO.output(self.PINS['EN']['Z'], GPIO.LOW)
        while not self._check_endstop('Z', False) and not self.stop_move.is_set():
            GPIO.output(self.PINS['STEP']['Z'], GPIO.HIGH)
            sleep(self.STEP_DELAY_US / 1_000_000)
            GPIO.output(self.PINS['STEP']['Z'], GPIO.LOW)
            sleep(self.STEP_DELAY_US / 1_000_000)
        GPIO.output(self.PINS['EN']['Z'], GPIO.HIGH)
        return
    
    def calibrate(self, wait: bool = True) -> bool:
        """
        Calibrate stage by moving to both endstops and measuring range
        Sets position limits for each axis
        
        Args:
            wait: If True, block until calibration completes
        
        Returns:
            True if calibration started successfully
        """
        if not self.initialized:
            print("Stage controller not initialized")
            return False
        if self.is_moving:
            print("Move already in progress")
            return False
        self.is_moving = True
        self.stop_move.clear()
        self.move_thread = Thread(target=self._execute_calibrate, daemon=True)
        self.move_thread.start()
        if wait:
            self.move_thread.join()
        return True
    
    def _execute_calibrate(self) -> None:
        """Execute calibration procedure (runs in separate thread)"""
        try:
            print("Calibrating stage...")
            self._execute_home()
            x_range = self._measure_axis_range('X')
            self.limits['X']['max'] = x_range
            y_range = self._measure_axis_range('Y')
            self.limits['Y']['max'] = y_range
            z_range = self._measure_axis_range('Z')
            self.limits['Z']['max'] = z_range
            with self.position_lock:
                self.position = [0.0, 0.0, 0.0]
            print(f"Calibration complete:")
            print(f"  X range: 0.0 to {x_range:.2f} mm")
            print(f"  Y range: 0.0 to {y_range:.2f} mm")
            print(f"  Z range: 0.0 to {z_range:.2f} mm")
        except Exception as e:
            print(f"Error during calibration: {e}")
        finally:
            self.is_moving = False
            if self.on_move_complete:
                self.on_move_complete()
        return
    
    def _measure_axis_range(self, axis: str) -> float:
        """
        Measure range of an axis by moving to positive endstop
        
        Args:
            axis: Axis to measure ('X', 'Y', or 'Z')
        
        Returns:
            Range in mm
        """
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]
        GPIO.output(self.PINS['DIR'][axis], GPIO.HIGH)
        GPIO.output(self.PINS['EN'][axis], GPIO.LOW)
        steps = 0
        while not self._check_endstop(axis, True) and not self.stop_move.is_set():
            GPIO.output(self.PINS['STEP'][axis], GPIO.HIGH)
            sleep(self.STEP_DELAY_US / 1_000_000)
            GPIO.output(self.PINS['STEP'][axis], GPIO.LOW)
            sleep(self.STEP_DELAY_US / 1_000_000)
            steps += 1
        GPIO.output(self.PINS['EN'][axis], GPIO.HIGH)
        range_mm = self._steps_to_mm(steps, axis)
        with self.position_lock:
            self.position[axis_idx] = range_mm
        GPIO.output(self.PINS['DIR'][axis], GPIO.LOW)
        GPIO.output(self.PINS['EN'][axis], GPIO.LOW)
        for _ in range(steps):
            if self.stop_move.is_set():
                break
            GPIO.output(self.PINS['STEP'][axis], GPIO.HIGH)
            sleep(self.STEP_DELAY_US / 1_000_000)
            GPIO.output(self.PINS['STEP'][axis], GPIO.LOW)
            sleep(self.STEP_DELAY_US / 1_000_000)
        GPIO.output(self.PINS['EN'][axis], GPIO.HIGH)
        with self.position_lock:
            self.position[axis_idx] = 0.0
        return range_mm
    
    def _check_endstop(self, axis: str, positive: bool) -> bool:
        """
        Check if endstop is triggered
        
        Args:
            axis: Axis to check ('X', 'Y', or 'Z')
            positive: True to check positive endstop, False for negative
        
        Returns:
            True if endstop is triggered
        """
        pin = self.PINS['ENDSTOP_POS'][axis] if positive else self.PINS['ENDSTOP_NEG'][axis]
        return GPIO.input(pin) == GPIO.LOW
    
    def _mm_to_steps(self, distance_mm: float, axis: str) -> int:
        """
        Convert mm to steps
        
        Args:
            distance_mm: Distance in mm
            axis: Axis ('X', 'Y', or 'Z')
        
        Returns:
            Number of steps (signed)
        """
        axis_key = f"{axis.lower()}_steps_per_mm"
        steps_per_mm = self.settings.saved_settings['motors'][axis_key]
        return int(distance_mm * steps_per_mm)
    
    def _steps_to_mm(self, steps: int, axis: str) -> float:
        """
        Convert steps to mm
        
        Args:
            steps: Number of steps (signed)
            axis: Axis ('X', 'Y', or 'Z')
        
        Returns:
            Distance in mm
        """
        axis_key = f"{axis.lower()}_steps_per_mm"
        steps_per_mm = self.settings.saved_settings['motors'][axis_key]
        return steps / steps_per_mm if steps_per_mm != 0 else 0
    
    def stop(self) -> None:
        """Emergency stop - halt all movement"""
        self.stop_move.set()
        if self.move_thread and self.move_thread.is_alive():
            self.move_thread.join(timeout=2.0)
        self.is_moving = False
        print("Stage movement stopped")
        return
    
    def cleanup(self) -> None:
        """Cleanup GPIO on shutdown"""
        if self.initialized:
            self.stop()
            for axis in ['X', 'Y', 'Z']:
                GPIO.output(self.PINS['EN'][axis], GPIO.HIGH)
            GPIO.cleanup()
            print("Stage controller cleaned up")
        return
    
    def __del__(self):
        """Destructor - cleanup GPIO"""
        self.cleanup()
        return