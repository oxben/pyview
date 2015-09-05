#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import math
import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

RotOffset   = 5.0
ScaleOffset = 0.1
MaxZoom     = 2.0
FrameRadius = 25.0
FrameWidth  = 10.0

Debug = True

class PhotoFrameItem(QGraphicsItem):

    def __init__(self, rect, parent = None, scene = None):
        super(PhotoFrameItem, self).__init__(parent, scene)
        self.rect = rect

    def boundingRect(self):
        return QRectF(self.rect)

    def paint(self, painter, option, widget = None):
        # painter.fillRect(QRectF(self.rect.left(), self.rect.top(),
        #                         self.rect.width(), FrameRadius/2), Qt.white)
        # painter.fillRect(QRectF(self.rect.left(), self.rect.top(),
        #                         FrameRadius/2, self.rect.height()), Qt.white)
        # painter.fillRect(QRectF(self.rect.right()-FrameRadius/2, self.rect.top(),
        #                         FrameRadius/2, self.rect.height()), Qt.white)
        # painter.fillRect(QRectF(self.rect.left(), self.rect.bottom()-FrameRadius/2,
        #                         self.rect.width(), FrameRadius/2), Qt.white)

        pen = painter.pen()
        pen.setColor(Qt.white)
        #pen.setWidth(FrameWidth)
        pen.setWidth(FrameRadius)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        # painter.drawRoundedRect(self.rect.left()+FrameRadius/2, self.rect.top()+FrameRadius/2,
        #                         self.rect.width()-FrameRadius, self.rect.height()-FrameRadius,
        #                         FrameRadius, FrameRadius)
        painter.drawRoundedRect(self.rect.left(), self.rect.top(),
                                self.rect.width(), self.rect.height(),
                                FrameRadius, FrameRadius)

class ImageView(QGraphicsView):

    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Connect signals
        # Is it necessary?
        QMetaObject.connectSlotsByName(self)
        self.dragImage = False

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        origx = self.pixmap.pixmap().size().width()/2
        origy = self.pixmap.pixmap().size().height()/2
        print(origx, origy)
        self.pixmap.setTransformOriginPoint(origx, origy)
        # XXX: setTransformationMode() seems buggy for scaling when using setTransform()
        # So translate before and after scaling
        # Example:
        # transform = self.pixmap.transform()
        # transform.translate(256.0, 256.0).scale(1.1, 1.1).rotate(10).translate(-256.0, -256.0)
        # self.pixmap.setTransform(transform)

        # Use bilinear filtering
        self.pixmap.setTransformationMode(Qt.SmoothTransformation)
        print(self.pixmap.transformOriginPoint())

    def setFrame(self, frame):
        self.frame = frame

    def keyReleaseEvent(self, event):
        global FrameRadius
        if Debug:
            print(event.key())
        if event.key() == Qt.Key_Slash:
            # Reset scale and rotation
            self.pixmap.setScale(1.0)
            self.pixmap.setRotation(0.0)
        elif event.key() == Qt.Key_Plus:
            FrameRadius += 1.0
            self.viewport().update()
        elif event.key() == Qt.Key_Minus:
            FrameRadius = max(0, FrameRadius - 1.0)
            self.viewport().update()

    def wheelEvent(self, event):
        scale = self.pixmap.scale()
        rot   = self.pixmap.rotation()
        if event.delta() > 0:
            if Debug:
                print("Zoom")
            rot += RotOffset
            if scale < MaxZoom:
                scale += ScaleOffset

            if event.modifiers() == Qt.ShiftModifier:
                self.pixmap.setRotation(self.pixmap.rotation() + RotOffset)
            elif self.pixmap.scale() < 2.0:
                self.pixmap.setScale(self.pixmap.scale() + ScaleOffset)
        else:
            if Debug:
                print("Unzoom")
            rot -= RotOffset
            if scale >= ScaleOffset*2:
                scale -= ScaleOffset

        modifiers = event.modifiers()
        if modifiers == Qt.NoModifier:
            self.pixmap.setScale(scale)
        elif modifiers == Qt.ShiftModifier:
            self.pixmap.setRotation(rot)
        elif modifiers == (Qt.ShiftModifier|Qt.ControlModifier):
            self.pixmap.setScale(scale)
            self.pixmap.setRotation(rot)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.pixmap.setPos(self.pixmap.pos() + (event.posF() - self.dragOrig))
            self.dragOrig = event.posF()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if Debug:
                print("Left button pressed")
            self.dragOrig = event.posF()

    # def mouseReleaseEvent (self, QMouseEvent event):

#
# Main
#

# Create an PyQT4 application object.
app = QApplication(sys.argv)

# The QWidget widget is the base class of all user interface objects in PyQt4.
w = QWidget()

# Set window title
w.setWindowTitle("PyView")
w.resize(512, 512)

# Create GraphicsView
gfxview = ImageView(w)
# Set OpenGL renderer
#gfxview.setViewport(QGLWidget())
# Add scene
scene = QGraphicsScene()
# Load pixmap and add it to the scene
pixmap = QPixmap(os.getcwd() + '/test.png')
pix = scene.addPixmap(pixmap)
gfxview.setPixmap(pix)
frame = PhotoFrameItem(QRect(0, 0, 512, 512))
fr = scene.addItem(frame)
gfxview.setFrame(fr)
gfxview.setScene(scene)

# Show window
w.show()
sys.exit(app.exec_())
