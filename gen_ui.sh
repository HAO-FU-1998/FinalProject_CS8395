#!/bin/bash

echo 'start gen...'

echo 'gen resources_rc.py'
rm resources_rc.py
pyrcc5 resources.qrc  >> resources_rc.py

echo 'gen mainwindow.py'
rm mainwindow.py
pyuic5  mainwindow.ui >> mainwindow.py

echo 'OK'

