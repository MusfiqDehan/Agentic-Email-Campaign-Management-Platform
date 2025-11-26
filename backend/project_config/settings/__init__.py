"""
Settings module initialization.
Imports the appropriate settings based on DJANGO_ENV environment variable.
"""

import os
from decouple import config

# Determine which settings to use
DJANGO_ENV = config("DJANGO_ENV", default="local")

if DJANGO_ENV == "production":
    from .production import *
elif DJANGO_ENV == "development":
    from .development import *
else:
    from .base import *