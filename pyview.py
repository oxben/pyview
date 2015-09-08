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
MaxZoom     = 1.0
FrameRadius = 15.0
FrameWidth  = 10.0
CollageSize = QRectF(0, 0, 1024, 1024)

Debug = True
OpenGLRender = False


class PhotoFrameItem(QGraphicsItem):

    def __init__(self, rect, parent = None, scene = None):
        super(PhotoFrameItem, self).__init__(parent, scene)
        self.rect = rect
        # Set flags
        self.setFlags(self.flags() | QGraphicsItem.ItemClipsChildrenToShape)

    def boundingRect(self):
        return QRectF(self.rect)

    def paint(self, painter, option, widget = None):
        pen = painter.pen()
        pen.setColor(Qt.white)
        #pen.setWidth(FrameWidth)
        pen.setWidth(FrameRadius)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(self.rect.left(), self.rect.top(),
                                self.rect.width(), self.rect.height(),
                                FrameRadius, FrameRadius)


class PhotoItem(QGraphicsPixmapItem):

    def __init__(self, pixmap, parent = None, scene = None):
        super(PhotoItem, self).__init__(pixmap, parent, scene)
        # Set transform origin to center of pixmap
        origx = self.pixmap().size().width()/2
        origy = self.pixmap().size().height()/2
        self.setTransformOriginPoint(origx, origy)
        # Use bilinear filtering
        self.setTransformationMode(Qt.SmoothTransformation)
        # Set flags
        self.setFlags(self.flags() |  
                      QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemStacksBehindParent)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        # Request keyboard events
        self.setFocus()

    def hoverLeaveEvent(self, event):
        self.clearFocus()

    def keyReleaseEvent(self, event):
        if Debug:
            print(event.key())
        if event.key() == Qt.Key_Slash:
            # Reset scale and rotation
            self.setScale(1.0)
            self.setRotation(0.0)

    def wheelEvent(self, event):
        scale = self.scale()
        rot   = self.rotation()
        if event.delta() > 0:
            if Debug:
                print("Zoom")
            rot += RotOffset
            if scale < MaxZoom:
                scale += ScaleOffset
        else:
            if Debug:
                print("Unzoom")
            rot -= RotOffset
            if scale >= ScaleOffset*2:
                scale -= ScaleOffset

        modifiers = event.modifiers()
        if modifiers == Qt.NoModifier:
            self.setScale(scale)
        elif modifiers == Qt.ShiftModifier:
            self.setRotation(rot)
        elif modifiers == (Qt.ShiftModifier|Qt.ControlModifier):
            self.setScale(scale)
            self.setRotation(rot)


class ImageView(QGraphicsView):

    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Connect signals: XXX: Is it necessary?
        #QMetaObject.connectSlotsByName(self)

    def keyReleaseEvent(self, event):
        global FrameRadius
        if Debug:
            print(event.key())
        key = event.key()
        if key == Qt.Key_Plus:
            # Increase frame width
            FrameRadius += 1.0
            self.viewport().update()
        elif key == Qt.Key_Minus:
            # Decrease frame width
            FrameRadius = max(0, FrameRadius - 1.0)
            self.viewport().update()
        elif key == Qt.Key_S:
            # Save collage to output file
            self.scene().clearSelection()
            image = QImage(CollageSize.width(), CollageSize.height(), QImage.Format_RGB32)
            image.fill(Qt.black)
            painter = QPainter(image)
            self.render(painter)
            image.save("out.png")
        else:
        # Pass event to default handler
            super(ImageView, self).keyReleaseEvent(event)
    
    def resizeEvent(self, event):
        self.fitInView(CollageSize, Qt.KeepAspectRatio)


def addPhoto(rect):
    frame = PhotoFrameItem(QRect(0, 0, rect.width(), rect.height()))
    frame.setPos(rect.x(), rect.y())
    photo = PhotoItem(QPixmap(os.getcwd() + '/test.png'))
    photo.setParentItem(frame)
    # Center photo in frame
    photo.setPos(rect.width()/2 - photo.pixmap().width()/2,
                 rect.height()/2 - photo.pixmap().height()/2)
    # Add frame to scene
    fr = scene.addItem(frame)


def create_3_2B_3_collage():
    # First column
    x = 0
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 4
    for y in range(0, 4):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))
        #addPhoto(x * photoWidth, y * photoHeight, photoWidth, photoHeight)
    # Second column
    x += photoWidth
    photoWidth  = CollageSize.width() / 2
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))
    # Third column
    x += photoWidth
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 3
    for y in range(0, 3):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))


def create_2_2B_2_collage():
    # First column
    x = 0
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))
        #addPhoto(x * photoWidth, y * photoHeight, photoWidth, photoHeight)
    # Second column
    x += photoWidth
    photoWidth  = CollageSize.width() / 2
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))
    # Third column
    x += photoWidth
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight))


def createGridCollage(numx , numy):
    photoWidth  = CollageSize.width() / numx
    photoHeight =  CollageSize.height() / numy
    for x in range(0, numx):
        for y in range(0, numy):
            addPhoto(QRect(x * photoWidth, y * photoHeight, photoWidth, photoHeight))


def create_3x3_collage():
    createGridCollage(3, 3)


def create_2x2_collage():
    createGridCollage(2, 2)
  
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
layout = QVBoxLayout()
w.setLayout(layout)

# Create GraphicsView
gfxview = ImageView()
layout.addWidget(gfxview)
gfxview.setBackgroundBrush(QBrush(Qt.white))

# Set OpenGL renderer
if OpenGLRender:
    gfxview.setViewport(QGLWidget())

# Add scene
scene = QGraphicsScene()

# Load pixmap and add it to the scene
#create_3_2B_3_collage()
create_2_2B_2_collage()
#create_3x3_collage()
#create_2x2_collage()

gfxview.setScene(scene)

# Show window
w.show()
sys.exit(app.exec_())
