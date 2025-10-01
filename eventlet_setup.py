# eventlet_setup.py
# This file must be imported before any other modules to properly patch threading
import eventlet
eventlet.monkey_patch()
