"""
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(pathname)s[%(lineno)d]: %(message)s"
)
"""
import eventlet
eventlet.monkey_patch(os=False)
