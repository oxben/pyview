#! /usr/bin/env python3

# Simple Photo Collage application
#
# Author: Oxben <oxben@free.fr>
#
# -*- coding: utf-8 -*-

import getopt
import math
import os
import sys
from urllib.parse import *

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsView, QGraphicsScene
from PyQt5.QtWidgets import QFileDialog

from PyQt5.QtGui import QPainter, QBrush, QPixmap, QImage

from PyQt5.QtCore import QRect, QRectF, Qt


RotOffset   = 5.0
ScaleOffset = 0.05
MaxZoom     = 2.0
FrameRadius = 15.0
FrameWidth  = 10.0
CollageAspectRatio = (2.0 / 3.0)
CollageSize = QRectF(0, 0, 1024, 1024 * CollageAspectRatio)
LimitDrag   = True
OutFileName = "out.png"

Debug = True
OpenGLRender = False

filenames = []


#-------------------------------------------------------------------------------
def error(msg):
    print(("Error: %s\n") % (msg))


#-------------------------------------------------------------------------------
class PhotoFrameItem(QGraphicsItem):
    '''The frame around a photo'''
    def __init__(self, rect, parent = None):
        super(PhotoFrameItem, self).__init__(parent)
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


#-------------------------------------------------------------------------------
class PhotoItem(QGraphicsPixmapItem):
    '''A photo item'''
    def __init__(self, pixmap, parent = None):
        super(PhotoItem, self).__init__(pixmap, parent)
        self.reset()
        # Use bilinear filtering
        self.setTransformationMode(Qt.SmoothTransformation)
        # Set flags
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemStacksBehindParent)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

    def setPixmap(self, pixmap):
        print("setPixmap():", pixmap.width(), pixmap.height())
        super(PhotoItem, self).setPixmap(pixmap)
        self.reset()

    def reset(self):
        # Center photo in frame
        if self.parentItem() != None:
            frameRect = self.parentItem().boundingRect()
            self.setPos((frameRect.width() / 2) - (self.pixmap().width() / 2),
                        (frameRect.height() / 2) - (self.pixmap().height() / 2))
        # Set transform origin to center of pixmap
        origx = self.pixmap().width() / 2
        origy = self.pixmap().height() / 2
        self.setTransformOriginPoint(origx, origy)
        # Reset transformation
        self.setScale(1.0)
        self.setRotation(0.0)

    def hoverEnterEvent(self, event):
        # Request keyboard events
        self.setFocus()

    def hoverLeaveEvent(self, event):
        self.clearFocus()

    def keyReleaseEvent(self, event):
        if Debug:
            print(event.key())
        if event.key() == Qt.Key_Slash:
            # Reset pos, scale and rotation
            self.reset()

    def mouseDoubleClickEvent(self, event):
        filename = QFileDialog.getOpenFileName(None, 'Open File', os.getcwd())
        print("Open file:", filename)
        self.setPixmap(QPixmap(filename[0]))

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
            if scale >= ScaleOffset * 2:
                scale -= ScaleOffset
        # Transform based on mouse position
        # XXX: doesn't work well
        #self.setTransformOriginPoint(event.pos())
        modifiers = event.modifiers()
        if modifiers == Qt.NoModifier:
            self.setScale(scale)
        elif modifiers == Qt.ShiftModifier:
            self.setRotation(rot)
        elif modifiers == (Qt.ShiftModifier|Qt.ControlModifier):
            self.setScale(scale)
            self.setRotation(rot)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.proposedAction() == Qt.CopyAction and event.mimeData().hasText():
            filePath = unquote(urlparse(event.mimeData().text().strip()).path)
            print(filePath)
            pixmap = QPixmap(filePath)
            if pixmap.width() > 0:
                self.setPixmap(pixmap)


#-------------------------------------------------------------------------------
class ImageView(QGraphicsView):

    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)
        # Hide scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def keyReleaseEvent(self, event):
        global FrameRadius
        global OutFileName
        if Debug:
            print(event.key())
        modifiers = event.modifiers()
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
            if (modifiers == Qt.NoModifier and not OutFileName) or \
               modifiers == Qt.ShiftModifier:
                OutFileName, filetype = QFileDialog.getSaveFileName(None, 'Save Collage', os.getcwd())
            elif modifiers == Qt.ControlModifier:
                return
            print("Collage saved to file:", OutFileName)

            self.scene().clearSelection()
            image = QImage(CollageSize.width(), CollageSize.height(), QImage.Format_RGB32)
            image.fill(Qt.black)
            painter = QPainter(image)
            self.render(painter)
            image.save(OutFileName)
            # Explicitely delete painter to avoid the following error:
            # "QPaintDevice: Cannot destroy paint device that is being painted" + SIGSEV
            del painter

        else:
            # Pass event to default handler
            super(ImageView, self).keyReleaseEvent(event)

    def heightForWidth(self, w):
        print("heightForWidth(%d)") % (w)
        return w

    def resizeEvent(self, event):
        self.fitInView(CollageSize, Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        # Filter wheel events
        items = self.items(event.pos())
        if Debug:
            print(items)
        if items:
            for item in items:
                if isinstance(item, PhotoItem):
                    super(ImageView, self).wheelEvent(event)


#-------------------------------------------------------------------------------
class CollageScene(QGraphicsScene):
    def __init__(self):
        super(CollageScene, self).__init__()

    def addPhoto(self, rect, filepath):
        print('addPhoto(%s)' % filepath)
        frame = PhotoFrameItem(QRect(0, 0, rect.width(), rect.height()))
        frame.setPos(rect.x(), rect.y())
        photo = PhotoItem(QPixmap(filepath))
        photo.setParentItem(frame)
        photo.reset()
        # Add frame to scene
        fr = self.addItem(frame)


#-------------------------------------------------------------------------------
class LoopIter:
    '''Infinite iterator: loop on list elements, wrapping to first element when last element is reached'''
    def __init__(self, l):
        self.i = 0
        self.l = l

    def __iter__(self):
        return self

    def next(self):
        item = self.l[self.i]
        self.i = (self.i + 1)  % len(self.l)
        return item

def create_3_2B_3_collage(scene):
    f = LoopIter(filenames)
    # First column
    x = 0
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 3
    for y in range(0, 3):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())
    # Second column
    x += photoWidth
    photoWidth  = CollageSize.width() / 2
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())
   # Third column
    x += photoWidth
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 3
    for y in range(0, 3):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())


def create_2_2B_2_collage(scene):
    f = LoopIter(filenames)
    # First column
    x = 0
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())
    # Second column
    x += photoWidth
    photoWidth  = CollageSize.width() / 2
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())
    # Third column
    x += photoWidth
    photoWidth  = CollageSize.width() / 4
    photoHeight =  CollageSize.height() / 2
    for y in range(0, 2):
        scene.addPhoto(QRect(x, y * photoHeight, photoWidth, photoHeight), f.next())


def createGridCollage(scene, numx , numy):
    f = LoopIter(filenames)
    photoWidth  = CollageSize.width() / numx
    photoHeight =  CollageSize.height() / numy
    for x in range(0, numx):
        for y in range(0, numy):
            scene.addPhoto(QRect(x * photoWidth, y * photoHeight, photoWidth, photoHeight), f.next())


def create_3x3_collage(scene):
    createGridCollage(scene, 3, 3)


def create_2x2_collage(scene):
    createGridCollage(scene, 2, 2)


def create_3x4_collage(scene):
    createGridCollage(scene, 3, 4)

#-------------------------------------------------------------------------------
def usage():
    print('Usage: ' +  os.path.basename(sys.argv[0]) + \
          'image1...imageN')
    print("\nOptions:\n")
    print("  -h         This help message")


def parse_args():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    except getopt.GetoptError as err:
        error(str(err))
        self.usage()
        sys.exit(1)

    for o, a in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)

    if len(args) == 0:
        error('At least one file must be specified on the command line')
        usage()
        sys.exit(1)

    for f in args:
        filenames.append(os.path.abspath(f))
        print(filenames)


def main():
    # Parse arguments
    parse_args()

    # Create an PyQt5 application object.
    app = QApplication(sys.argv)

    # The QWidget widget is the base class of all user interface objects in PyQt5.
    w = QWidget()

    # Set window title
    w.setWindowTitle("PyView")
    w.resize(512, 512 * CollageAspectRatio)
    layout = QHBoxLayout()
    w.setLayout(layout)

    # Create GraphicsView
    gfxview = ImageView()
    layout.addWidget(gfxview)
    gfxview.setBackgroundBrush(QBrush(Qt.white))

    # Set OpenGL renderer
    if OpenGLRender:
        gfxview.setViewport(QGLWidget())

    # Add scene
    scene = CollageScene()

    # Load pixmap and add it to the scene
    #create_3_2B_3_collage()
    #create_2_2B_2_collage()
    #create_3x3_collage()
    #create_2x2_collage()
    #createGridCollage(2, 3)
    create_3x4_collage(scene)

    gfxview.setScene(scene)

    # Show window
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
