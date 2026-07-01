[app]

# (str) Title of your application
title = Corn Leaf Disease

# (str) Package name
package.name = corn_disease_app

# (str) Package domain (needed for android packaging)
package.domain = org.corn.disease

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,txt,tflite

# (list) List of directory to exclude (comma separated)
source.exclude_dirs = tests, bin, .venv, .git, reports

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*, models/*

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3, kivy==2.3.1, kivymd==1.2.0, pillow, numpy, tflite-runtime, android, plyer

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Use fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = CAMERA, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 24

# (int) Android NDK API to use
android.ndk_api = 24

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data directory (True) or public (False)
android.private_storage = True

# (list) Android architectures to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) Allow service to be run in background
android.allow_backup = True

# (str) The Android card name (app name shown in launcher)
android.app_name = Corn Leaf Disease

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/presplash.png

# (str) Custom python-for-android directory
p4a.source_dir = /content/python-for-android

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
