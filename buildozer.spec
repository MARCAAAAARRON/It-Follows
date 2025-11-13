[app]

# (str) Title of your application
title = It Follows

# (str) Package name
package.name = itfollows

# (str) Package domain (needed for android/ios packaging)
package.domain = org.itfollows

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) List of inclusions using entry points
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.2.1,kivymd,pillow

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = 2.2.1

# (list) Permissions
android.permissions = INTERNET, VIBRATE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 20

# (str) Android NDK version to use
#android.ndk = 23b

# (bool) enable --auto-add-overlay if your app has an overlay
#android.allow_backup = True

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (bool) Enable AndroidX support
#android.enable_androidx = True

# (str) Orientation (one of landscape, portrait, sensor, or user)
orientation = portrait

# (list) Application specific compilation options
# (list) The Python modules to include in the distribution
#options.include_exts = py,png,jpg,kv,atlas

# (str) The format used to package the app for release mode
# (default is a debug build)
#android.release_artifact = bin/ItFollows-{version}-release.apk
#android.debug_artifact = bin/ItFollows-{version}-debug.apk

# (str) The format used to package the app for debug mode
# (default is a debug build)
#android.debug_artifact = bin/ItFollows-{version}-debug.apk

# (bool) Indicates whether the app should be fullscreen or not
fullscreen = 1

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait, sensor, or user)
#orientation = portrait

# (bool) Indicates if the application should be fullscreen or not
#fullscreen = 0

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# (str) The format used to package the app for release mode
# (default is a debug build)
#android.release_artifact = bin/ItFollows-{version}-release.apk
#android.debug_artifact = bin/ItFollows-{version}-debug.apk

# (str) The format used to package the app for debug mode
# (default is a debug build)
#android.debug_artifact = bin/ItFollows-{version}-debug.apk

# (bool) Skip byte compile for .py files
# (useful for debugging the application)
#android.no-byte-compile-python = False

# (list) The Python modules to exclude from the distribution
# (useful to exclude some test modules)
#android.exclude_py_modules = test, test_*
