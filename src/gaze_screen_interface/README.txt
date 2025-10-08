# Gaze Screen Interface

A modular PySide6-based screen interface for robot control with ROS2 integration and gaze interaction support.

## Features

- ✅ **Modular screen architecture** - Easy to add new screens
- ✅ **ROS2 integration** - Publishes button positions, subscribes to gaze and button status
- ✅ **Gaze interaction support** - Visual feedback for dwell time progress
- ✅ **Mouse fallback** - Full functionality with mouse for testing
- ✅ **Debug visualization** - On-screen gaze point display
- ✅ **Animated buttons** - Custom widgets with visual feedback

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  PySide6 UI     │────────>│  Button Manager  │
│  (Screens)      │         │  (Geometry)      │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │                           v
         │                  ┌────────────────┐
         │                  │   ROS Bridge   │
         │                  └────────┬───────┘
         │                           │
         v                           v
    ┌────────────────────────────────────────┐
    │           ROS2 Network                 │
    └────────────────────────────────────────┘
              │                    │
              v                    v
    ┌──────────────────┐  ┌──────────────────┐
    │ Dwell Time Mgr   │  │  Gaze Controller │
    │ (/active_button) │  │ (/corrected_gaze)│
    └──────────────────┘  └──────────────────┘
```

## Installation

### Prerequisites

```bash
# Install PySide6
pip install PySide6

# Ensure ROS2 is installed and sourced
source /opt/ros/humble/setup.bash  # or your ROS2 distro
```

### Build

```bash
# In your ROS2 workspace
cd ~/ros2_ws/src
git clone <your-repo>

cd ~/ros2_ws
colcon build --packages-select gaze_screen_interface
source install/setup.bash
```

### Custom Messages

Before running, you need to create/source your custom message packages:

1. **DiegeticButton2D.msg** and **DiegeticButton2DArray.msg** in `diegetic_transform_engine` package
2. **ButtonStatus.msg** in your package

Update `ros_bridge.py` to import your actual message types:

```python
from diegetic_transform_engine.msg import DiegeticButton2D, DiegeticButton2DArray
from your_package.msg import ButtonStatus
```

## Usage

### Launch the Interface

```bash
ros2 run gaze_screen_interface gaze_interface
```

### Testing Without Gaze Hardware

The interface works fully with mouse:
- Click buttons directly to trigger actions
- Button status updates can be simulated by publishing to `/active_button`

```bash
# Simulate button hover
ros2 topic pub /active_button your_package/ButtonStatus "..."
```

### Topics

**Published:**
- `/screen_buttons` (DiegeticButton2DArray) - Current on-screen button positions

**Subscribed:**
- `/active_button` (ButtonStatus) - Button state updates from Dwell Time Manager
- `/gaze_controller/corrected_gaze` (PointStamped) - Gaze coordinates for debug display

## Project Structure

```
gaze_screen_interface/
├── gaze_screen_interface/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── ros_bridge.py           # ROS2 communication
│   ├── button_manager.py       # Button geometry management
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py      # Main window & navigation
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── base_screen.py  # Abstract base class
│       │   ├── main_menu.py    # Main menu (3 mode buttons)
│       │   └── translation_screen.py  # Example sub-screen
│       └── widgets/
│           ├── __init__.py
│           └── gaze_button.py  # Custom button widget
├── setup.py
├── package.xml
└── README.md
```

## Adding New Screens

1. **Create screen class** inheriting from `BaseScreen`:

```python
from .base_screen import BaseScreen

class MyNewScreen(BaseScreen):
    def __init__(self, parent=None):
        super().__init__("my_screen", parent)
        self._setup_ui()
    
    def _setup_ui(self):
        btn = self.add_gaze_button(
            "btn_action",
            "Do Something",
            lambda: print("Action!")
        )
        self.layout.addWidget(btn)
```

2. **Register in MainWindow** (`main_window.py`):

```python
my_screen = MyNewScreen()
my_screen.navigate_to.connect(self.navigate_to_screen)
my_screen.buttons_changed.connect(self._schedule_button_publish)
self.screens["my_screen"] = self.screen_stack.addWidget(my_screen)
```

3. **Navigate to it** from another screen:

```python
self.navigate_to.emit("my_screen")
```

## Design Decisions & Recommendations

### ✅ What Works Well

1. **Separation of concerns** - UI, ROS2, and geometry management are decoupled
2. **BaseScreen abstraction** - Makes adding screens trivial
3. **Normalized coordinates** - Button positions sent as [0,1] range, independent of screen resolution
4. **Qt signals for ROS2** - Clean integration without blocking UI thread

### ⚠️ Current Limitations

1. **No overlay support yet** - Submenu overlay mentioned in requirements not implemented
2. **Only 2 screens** - Rotation and grasping screens need to be added
3. **Mock messages** - Replace mock classes with actual imports
4. **No image support** - Buttons currently text-only (easy to add via QIcon)
5. **No button animations beyond hover** - Could add more sophisticated animations

### 🔧 Suggested Improvements

1. **Add `interactable` flag** to buttons instead of not publishing them:
   ```python
   # In DiegeticButton2D.msg
   bool interactable  # false when overlayed/disabled
   ```

2. **Add sequence IDs** to prevent race conditions:
   ```python
   # In DiegeticButton2DArray.msg
   uint32 sequence_id
   ```

3. **Reduce message size** in ButtonStatus:
   - Remove redundant `DiegeticButton2D button` field
   - Just send `button_id`, `status`, `percent`

4. **Configuration file** for button layouts (YAML):
   ```yaml
   main_menu:
     buttons:
       - id: btn_translation
         text: "Translation Mode"
         icon: "icons/translate.png"
   ```

5. **State machine** for complex navigation with history:
   ```python
   # Track navigation history for back button
   self.screen_history = []
   ```

## Troubleshooting

### Buttons not appearing in ROS topics

- Check that screen's `buttons_changed` signal is connected
- Verify button manager is receiving correct geometry
- Check ROS2 topic: `ros2 topic echo /screen_buttons`

### Gaze point not showing

- Verify gaze topic is publishing: `ros2 topic hz /gaze_controller/corrected_gaze`
- Check that coordinates are normalized [0,1]
- Toggle visibility in code if needed

### Button status not updating

- Check Dwell Time Manager is running
- Verify topic names match: `/active_button`
- Check message definition compatibility

## Next Steps

1. Implement rotation and grasping screens
2. Add overlay/submenu support with `interactable` flag
3. Replace mock message classes with actual imports
4. Add button icons/images
5. Implement configuration file loading
6. Add more sophisticated animations
7. Add unit tests

## License

MIT License - See LICENSE file for details