import cv2
from PySide2 import QtGui


def cv_img2qimage(img=cv2.imread('')):
    if len(img.shape) == 3:
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            qimg = QtGui.QImage(img.data, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
            qimg = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_ARGB32)
        elif img.shape[2] == 1:
            qimg = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_Grayscale8)
        else:
            print("Unsupported cv image tpye!")
            return QtGui.QImage()
    elif len(img.shape) == 2:
        qimg = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_Grayscale8)
    return qimg

