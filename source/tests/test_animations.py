import pytest
from source.animations.animation import Animation
from source.animations.animation_functions import dots
import source.constants as cons
import threading
import time


@pytest.fixture
def animation():
    return Animation(dots)


def test_animation(animation, capsys):
    """Tests the full functionality of the Animation class with the dots animation function."""
    dots_to_count = 3  # Arbitrary choice, can be changed as needed/wanted, but will affect the test run time.

    # Initialization parameters are set correctly
    assert animation.action == dots
    assert animation.time_delay == cons.ANIMATION_DELAY
    assert animation._run_flag is False
    assert isinstance(animation._thread, threading.Thread)

    # start() method correctly sets the run flag to True
    animation.start()
    assert animation._run_flag is True
    time.sleep(dots_to_count * animation.time_delay)  # Let the animation run for a bit

    # stop() method correctly sets the run flag to False
    animation.stop()
    assert animation._run_flag is False

    # Expected number of dots are printed to the screen
    captured_animation = capsys.readouterr()
    assert captured_animation.out.count(".") == dots_to_count

    return
