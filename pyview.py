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

class PhotoItem(QGraphicsPixmapItem):

    def __init__(self, pixmap, parent = None, scene = None):
        super(PhotoItem, self).__init__(pixmap, parent, scene)
        # Set transform origin to center of pixmap
        origx = self.pixmap().size().width()/2
        origy = self.pixmap().size().height()/2
        self.setTransformOriginPoint(origx, origy)
        print("origin:", origx, origy)
        # Use bilinear filtering
        self.setTransformationMode(Qt.SmoothTransformation)
        # XXX: setTransformationMode() seems buggy for scaling when using setTransform()
        # So translate before and after scaling
        # Example:
        # transform = self.pixmap.transform()
        # transform.translate(256.0, 256.0).scale(1.1, 1.1).rotate(10).translate(-256.0, -256.0)
        # self.pixmap.setTransform(transform)
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

    # def mouseMoveEvent(self, event):
    #     if event.buttons() == Qt.LeftButton:
    #         self.setPos(self.pos() + (event.pos() - self.dragOrig))
    #         self.dragOrig = event.pos()

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         if Debug:
    #             print("Left button pressed")
    #         self.dragOrig = event.pos()
    #         app.setOverrideCursor(Qt.ClosedHandCursor)

    # def mouseReleaseEvent (self, event):
    #     if event.button() == Qt.LeftButton:
    #         app.restoreOverrideCursor()


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
        if event.key() == Qt.Key_Plus:
            FrameRadius += 1.0
            self.viewport().update()
        elif event.key() == Qt.Key_Minus:
            FrameRadius = max(0, FrameRadius - 1.0)
            self.viewport().update()
        else:
        # Pass event to default handler
            super(ImageView, self).keyReleaseEvent(event)
    
    def resizeEvent(self, event):
        self.fitInView(CollageSize, Qt.KeepAspectRatio)

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
photosX = 2
photosY = 3
photoWidth  = CollageSize.width() / photosX
photoHeight =  CollageSize.height() / photosY
print("photoWidth=", photoWidth)
print("photoHeight=", photoHeight)
for x in range (0, photosX):
    for y in range (0, photosY):
        # Create frame and photo
        frame = PhotoFrameItem(QRect(0, 0, photoWidth, photoHeight))
        frame.setPos(x * photoWidth, y * photoHeight)
        photo = PhotoItem(QPixmap(os.getcwd() + '/test.png'))
        photo.setParentItem(frame)
        # Center photo in frame
        photo.setPos(photoWidth/2 - photo.pixmap().width()/2,
                     photoHeight/2 - photo.pixmap().height()/2)
        # Add frame to scene
        fr = scene.addItem(frame)

gfxview.setScene(scene)

# Show window
w.show()
sys.exit(app.exec_())
