from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtSvg
from PyQt5 import QtCore
from PyQt5 import QtOpenGL
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QToolTip
import math
from enum import Enum, unique
import sys
import cv2
import numpy as np
import gc
# from keras.models import load_model
# from opencv_processing import cv_common

try:
    from OpenGL import GL
except ImportError:
    print("No OpenGL support on current platform!")
    sys.exit(1)


def angle(v1, v2):
    l1 = np.sqrt(v1.dot(v1))
    l2 = np.sqrt(v2.dot(v2))
    return np.arccos(v1.dot(v2) / (l1 * l2))


def calculate_angle_3vec(pos0, pos1, pos2, pos3):
    list_of_angle = [
        angle(
            np.array([pos1[0] - pos0[0], pos1[1] - pos0[1]]),
            np.array([pos2[0] - pos0[0], pos2[1] - pos0[1]])),
        angle(
            np.array([pos1[0] - pos0[0], pos1[1] - pos0[1]]),
            np.array([pos3[0] - pos0[0], pos3[1] - pos0[1]])),
        angle(
            np.array([pos2[0] - pos0[0], pos2[1] - pos0[1]]),
            np.array([pos3[0] - pos0[0], pos3[1] - pos0[1]]))]
    return list_of_angle


def sort_pos(pos0, pos1, pos2, pos3):
    sorted_pos = []
    min_line1y = min(pos0[1], pos1[1])
    min_line2y = min(pos2[1], pos3[1])
    if min_line1y < min_line2y:
        if pos0[0] < pos1[0]:
            sorted_pos.append(pos0)
            sorted_pos.append(pos1)
        else:
            sorted_pos.append(pos1)
            sorted_pos.append(pos0)
        if pos2[0] < pos3[0]:
            sorted_pos.append(pos2)
            sorted_pos.append(pos3)
        else:
            sorted_pos.append(pos3)
            sorted_pos.append(pos2)
    else:
        if pos2[0] < pos3[0]:
            sorted_pos.append(pos2)
            sorted_pos.append(pos3)
        else:
            sorted_pos.append(pos3)
            sorted_pos.append(pos2)
        if pos0[0] < pos1[0]:
            sorted_pos.append(pos0)
            sorted_pos.append(pos1)
        else:
            sorted_pos.append(pos1)
            sorted_pos.append(pos0)

    return sorted_pos


def get_lx_ly_sorted_pos(pos0, pos1, pos2, pos3):
    vec0 = np.array([math.fabs(pos1[0] - pos0[0]), math.fabs(pos1[1] - pos0[1])])
    vec1 = np.array([math.fabs(pos2[0] - pos0[0]), math.fabs(pos2[1] - pos0[1])])
    vec2 = np.array([pos3[0] - pos1[0], pos3[1] - pos1[1]])
    vec3 = np.array([pos3[0] - pos2[0], pos3[1] - pos2[1]])
    sorted_pos = []
    lx = 0
    ly = 0
    ang_x1 = angle(vec0, np.array([1, 0]))
    ang_x2 = angle(vec1, np.array([1, 0]))
    if ang_x1 < ang_x2:
        lx1 = np.sqrt(vec0.dot(vec0))
        lx2 = np.sqrt(vec3.dot(vec3))
        lx = max(lx1, lx2)
        ly1 = np.sqrt(vec1.dot(vec1))
        ly2 = np.sqrt(vec2.dot(vec2))
        ly = max(ly1, ly2)
        sorted_pos = sort_pos(pos0, pos1, pos2, pos3)
    else:
        ly1 = np.sqrt(vec0.dot(vec0))
        ly2 = np.sqrt(vec3.dot(vec3))
        ly = max(ly1, ly2)
        lx1 = np.sqrt(vec1.dot(vec1))
        lx2 = np.sqrt(vec2.dot(vec2))
        lx = max(lx1, lx2)
        sorted_pos = sort_pos(pos0, pos2, pos1, pos3)
    return lx, ly, sorted_pos


@unique
class resize_rect_type(Enum):
    resize_X = 1
    resize_Y = 2
    resize_XY = 3


@unique
class mode_type(Enum):
    auto_select = 1
    select = 2
    run = 3


label = \
    [
        'BG',
        'yb',
        'deng1',
        'deng2',
        'kaiguan',
        'baohu',
        'mianban',
        'ping',
    ]


class detect_rect:
    def __init__(self, box, name):
        self.box = box
        self.name = name


class my_ellipse_item(QtWidgets.QGraphicsEllipseItem):
    def __init__(self):
        QToolTip.hideText()
        super(my_ellipse_item, self).__init__()
        self.__pen_width = 3
        self.__rect_size = 20
        self.__resize_rect_type = resize_rect_type.resize_XY
        outline = QtGui.QPen(QtGui.QColor(0, 255, 0), self.__pen_width, QtCore.Qt.PenStyle.SolidLine)
        outline.setCosmetic(True)
        self.setPen(outline)
        self.setBrush(QtGui.QBrush(QtGui.QColor(230, 0, 0, 150)))
        self.setRect(QtCore.QRectF(0, 0, self.__rect_size, self.__rect_size))
        self.setStartAngle(16 * 0)
        self.setSpanAngle(16 * 360)
        self.setVisible(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        self.setZValue(2)

    def set_resize_rect_type(self, resize_rect_type_=resize_rect_type.resize_XY):
        self.__resize_rect_type = resize_rect_type_

    def get_rect_size(self):
        return self.boundingRect().width() - self.__pen_width, self.boundingRect().height() - self.__pen_width

    def get_pos(self):
        return self.pos().x() + self.__rect_size / 2, self.pos().y() + self.__rect_size / 2


class my_rect_item(QtWidgets.QGraphicsRectItem):
    def __init__(self, a, b, c, d, cnn_model_dict, class_id):
        super(my_rect_item, self).__init__(a, b, c, d)
        self.__scale = 1
        self.__pen_width = 3
        self.__class_id = class_id
        self.__resize_rect_type = resize_rect_type.resize_XY
        self.__cnn_model_dict = cnn_model_dict
        for it in cnn_model_dict.keys():
            if it in class_id:
                self.__cnn_model = it
                break
            else:
                self.__cnn_model = ''
        if not self.__cnn_model:
            self.__cnn_model = ''
        self.__signal_ref = ''
        self.__set_model_act = QtWidgets.QAction()
        self.__set_model_act.setObjectName('action_set_model')
        self.__set_model_act.setText(QtWidgets.QApplication.translate("my_rect_item", "Set CNN Model", None, -1))
        self.__set_model_act.triggered.connect(self.__set_model)
        self.__set_signal_ref_act = QtWidgets.QAction()
        self.__set_signal_ref_act.setObjectName('action_set_signal_ref')
        self.__set_signal_ref_act.setText(QtWidgets.QApplication.translate("my_rect_item", "Set Signal Ref", None, -1))
        self.__set_signal_ref_act.triggered.connect(self.__set_signal_ref)
        outline = QtGui.QPen(QtGui.QColor(255, 0, 0), self.__pen_width, QtCore.Qt.PenStyle.SolidLine)
        outline.setCosmetic(True)
        self.setPen(outline)
        self.setToolTip('class_name: '+self.__class_id+'\n'+'model: '+self.__cnn_model+'\n'+'signal ref: '+self.__signal_ref)
        # self.setBrush(QtCore.Qt.BrushStyle.DiagCrossPattern)
        self.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 230, 150)))
        self.setVisible(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)

        self.setZValue(2)

    def __set_model(self):
        show_text = []
        for it in self.__cnn_model_dict.keys():
            show_text.append(it)
        (text, bool_) = QtWidgets.QInputDialog.getItem(None, "Select model", 'model', show_text, 0, False)
        if bool_:
            self.__cnn_model = text
        self.setToolTip('class_name: '+self.__class_id+'\n'+'model: '+self.__cnn_model+'\n'+'signal ref: '+self.__signal_ref)

    def __set_signal_ref(self):
        (text, bool_) = QtWidgets.QInputDialog.getText(None, "Set Signal Ref", "Signal Ref")
        if bool_:
            self.__signal_ref = text
        self.setToolTip('class_name: '+self.__class_id+'\n'+'model: '+self.__cnn_model+'\n'+'signal ref: '+self.__signal_ref)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        factor = math.pow(1.05, event.delta() / 240.0)
        if self.__resize_rect_type == resize_rect_type.resize_X:
            self.setRect(self.rect().x(), self.rect().y(), (self.boundingRect().width() - self.__pen_width) * factor,
                         self.boundingRect().height() - self.__pen_width)
        elif self.__resize_rect_type == resize_rect_type.resize_Y:
            self.setRect(self.rect().x(), self.rect().y(), self.boundingRect().width() - self.__pen_width,
                         (self.boundingRect().height() - self.__pen_width) * factor)
        else:
            self.setRect(self.rect().x(), self.rect().y(), (self.boundingRect().width() - self.__pen_width) * factor,
                         (self.boundingRect().height() - self.__pen_width) * factor)
        event.accept()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.RightButton:
            menu = QtWidgets.QMenu()
            menu.addAction(self.__set_model_act)
            menu.addAction(self.__set_signal_ref_act)
            menu.exec_(event.screenPos())

            event.accept()

    def set_resize_rect_type(self, resize_rect_type_=resize_rect_type.resize_XY):
        self.__resize_rect_type = resize_rect_type_

    def get_rect_size(self):
        return int(self.boundingRect().width() - self.__pen_width), int(self.boundingRect().height() - self.__pen_width)

    def get_pos(self):
        return int(self.pos().x()), int(self.pos().y())

    def get_cnn_model(self):
        return self.__cnn_model

    def get_signal_ref(self):
        return self.__signal_ref


class GraphicsView(QtWidgets.QGraphicsView):

    @unique
    class RenderType(Enum):
        Native = 1
        OpenGL = 2
        Image = 3

    class_result_output = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)

        self.__m_image = QtGui.QImage()
        self.__m_svg_item = QtSvg.QGraphicsSvgItem()
        self.__m_background_item = QtWidgets.QGraphicsRectItem()
        self.__m_outline_item = QtWidgets.QGraphicsRectItem()

        self.__detect_rect = []

        self.__resize_rect_type = resize_rect_type.resize_XY

        self.__m_render_type = self.RenderType.Native

        self.__ctrl_pressed = False

        self.__place_rectangle_flag = False
        self.__place_ellipse_flag = False
        self.__remove_rectangle_flag = False

        self.__scale = 1

        self.__transform = False

        self.__mode = mode_type.select

        self.__image = None

        self.__file_name = None

        self.__draw_background = True
        self.__draw_outline = True

        self.__video_timer = QTimer()
        self.__video_timer.timeout.connect(self.__video)

        self.__vcap = None

        self.__ncs_net = None

        self.__sorted_pos = []
        self.__lx = 0
        self.__ly = 0
        self.__rect_pos = []
        self.__perspective_transform_para = None

        self.__cnn_model_dict = {
            'deng2':  cv2.dnn.readNetFromTensorflow('light1/model.pb',  'light1/model.pbtxt'),
            'kaiguan': cv2.dnn.readNetFromTensorflow('switch1/model.pb', 'switch1/model.pbtxt')}
        self.__cnn_model_dict['deng2'].setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.__cnn_model_dict['deng2'].setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.__cnn_model_dict['kaiguan'].setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.__cnn_model_dict['kaiguan'].setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)

        self.__class_result = {}

        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        tile_pixmap = QtGui.QPixmap(64, 64)
        tile_pixmap.fill(QtGui.QColor(255, 255, 255))
        tile_painter = QtGui.QPainter(tile_pixmap)
        color = QtGui.QColor(220, 220, 220)
        tile_painter.fillRect(0, 0, 32, 32, color)
        tile_painter.fillRect(32, 32, 32, 32, color)
        tile_painter.end()
        self.setBackgroundBrush(QtGui.QBrush(tile_pixmap))

        self.mDragWindow = False
        self.mMousePoint = QtCore.QPoint()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            self.__ctrl_pressed = True

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Control:
            self.__ctrl_pressed = False

    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.__ctrl_pressed:
            factor = math.pow(1.2, event.angleDelta().y() / 240.0)
            QtWidgets.QGraphicsView.scale(self, factor, factor)
            event.accept()
        else:
            list_of_item = self.scene().items()
            for item in list_of_item:
                if item.isSelected():
                    item.set_resize_rect_type(self.__resize_rect_type)
            QtWidgets.QGraphicsView.wheelEvent(self, event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if (event.button() == QtCore.Qt.LeftButton) and self.__place_rectangle_flag:
            scene_mouse_pos = self.mapToScene(event.pos())
            self.place_rectangle(scene_mouse_pos.x(), scene_mouse_pos.y(), 60, 60, 'TODO')
            event.accept()
        elif (event.button() == QtCore.Qt.LeftButton) and self.__place_ellipse_flag:
            scene_mouse_pos = self.mapToScene(event.pos())
            self.place_ellipse(scene_mouse_pos.x(), scene_mouse_pos.y())
            event.accept()
        elif (event.button() == QtCore.Qt.LeftButton) and self.__remove_rectangle_flag:
            list_of_item = self.scene().items()
            for item in list_of_item:
                if item.isSelected():
                    self.scene().removeItem(item)
        else:
            QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def paintEvent(self, event: QtGui.QPaintEvent):
        if self.__m_render_type == self.RenderType.Image:
            if self.__m_image.size() != self.viewport().size():
                self.__m_image = QtGui.QImage(self.viewport().size(), QtGui.QImage.Format_ARGB32_Premultiplied)

            image_painter = QtGui.QPainter(self.__m_image)
            QtWidgets.QGraphicsView.render(self, image_painter)
            image_painter.end()

            p = QtGui.QPainter(self.viewport())
            p.drawImage(0, 0, self.__m_image)
        else:
            QtWidgets.QGraphicsView.paintEvent(self, event)

    def set_render(self, render_type=RenderType.Native):
        self.__m_render_type = render_type
        if self.__m_render_type == self.RenderType.OpenGL:
            print("render with openGL")
            self.setViewport(QtOpenGL.QGLWidget(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers)))
        else:
            print("render with native")
            self.setViewport(QtWidgets.QWidget())

    def set_view_background(self, enable=True):
        self.__m_background_item.setVisible(enable)
        self.__draw_background = enable
        print("Draw background:", self.__draw_background)

    def set_view_outline(self, enable=True):
        self.__m_outline_item.setVisible(enable)
        self.__draw_outline = enable
        print("Draw outline:", self.__draw_outline)

    def open_file(self, file_name=''):
        if file_name.endswith('.svg'):
            scene = self.scene()
            svg_item = QtSvg.QGraphicsSvgItem(file_name)

            if not svg_item.renderer().isValid():
                return False

            scene.clear()
            self.resetTransform()

            self.__m_svg_item = svg_item
            self.__m_svg_item.setFlags(QtWidgets.QGraphicsItem.ItemClipsToShape)
            self.__m_svg_item.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
            self.__m_svg_item.setZValue(0)

            self.__m_background_item = QtWidgets.QGraphicsRectItem(self.__m_svg_item.boundingRect())
            self.__m_background_item.setBrush(QtGui.QColor(255, 255, 255))
            self.__m_background_item.setPen(QtCore.Qt.PenStyle.NoPen)
            self.__m_background_item.setVisible(self.__draw_background)
            self.__m_background_item.setZValue(-1)

            self.__m_outline_item = QtWidgets.QGraphicsRectItem(self.__m_svg_item.boundingRect())
            outline = QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.PenStyle.DashLine)
            outline.setCosmetic(True)
            self.__m_outline_item.setPen(outline)
            self.__m_outline_item.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            self.__m_outline_item.setVisible(self.__draw_outline)
            self.__m_outline_item.setZValue(1)

            scene.addItem(self.__m_background_item)
            scene.addItem(self.__m_svg_item)
            scene.addItem(self.__m_outline_item)

            scene.setSceneRect(self.__m_outline_item.boundingRect().adjusted(0, 0, 0, 0))

        elif file_name.endswith('.jpg'):
            img = cv2.imread(file_name)
            self.__file_name = file_name
            self.show_image(img)

    def show_image(self, opencv_img):
        # self.__image = opencv_img
        scene = self.scene()

        if len(opencv_img.shape) == 3:
            ly, lx, dep = opencv_img.shape
            bytesPerLine = dep * lx
            opencv_img = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2RGB)
            opencv_img = QtGui.QImage(opencv_img.data, lx, ly, bytesPerLine, QtGui.QImage.Format_RGB888)

            scene.clear()
            gc.collect()
            # self.resetTransform()
            scene.addPixmap(QtGui.QPixmap.fromImage(opencv_img))

            self.__m_background_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(opencv_img.rect().topLeft(), opencv_img.rect().bottomRight()))

            self.__m_background_item.setBrush(QtGui.QColor(255, 255, 255))
            # self.__m_background_item.setPen(QtCore.Qt.PenStyle.NoPen)
            self.__m_background_item.setVisible(self.__draw_background)
            self.__m_background_item.setZValue(-1)

            self.__m_outline_item = QtWidgets.QGraphicsRectItem(QtCore.QRectF(opencv_img.rect().topLeft(), opencv_img.rect().bottomRight()))
            outline = QtGui.QPen(QtGui.QColor(0, 0, 0), 2, QtCore.Qt.PenStyle.DashLine)
            outline.setCosmetic(True)
            self.__m_outline_item.setPen(outline)
            # self.__m_outline_item.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            self.__m_outline_item.setVisible(self.__draw_outline)
            self.__m_outline_item.setZValue(1)

            for it in self.__detect_rect:
                self.place_rectangle(x=it.box[0], y=it.box[1], w_x=it.box[2], w_y=it.box[3], name=it.name)

            scene.addItem(self.__m_background_item)
            scene.addItem(self.__m_outline_item)
            scene.setSceneRect(self.__m_outline_item.boundingRect().adjusted(0, 0, 0, 0))

    def zoom_canvas(self, scale=1):
        self.__scale = scale
        QtWidgets.QGraphicsView.scale(self, self.__scale, self.__scale)

    def place_rectangle(self, x=0, y=0, w_x=60, w_y=60, name=''):
        # print('rect = {} {} {} {}'.format(x, y, w_x, w_y))
        scene = self.scene()
        # self.resetTransform()
        rect_item = my_rect_item(0, 0, w_x, w_y, self.__cnn_model_dict, name)
        rect_item.moveBy(x, y)
        scene.addItem(rect_item)
        scene.setSceneRect(self.__m_outline_item.boundingRect().adjusted(0, 0, 0, 0))

    def place_ellipse(self, x=0, y=0):
        scene = self.scene()
        # self.resetTransform()
        ellipse_item = my_ellipse_item()
        ellipse_item.moveBy(x, y)
        scene.addItem(ellipse_item)
        scene.setSceneRect(self.__m_outline_item.boundingRect().adjusted(0, 0, 0, 0))

    def set_place_rectangle(self, flag=False):
        self.__place_rectangle_flag = flag

    def set_place_ellipse(self, flag=False):
        self.__place_ellipse_flag = flag

    def set_remove_rectangle(self, flag=False):
        self.__remove_rectangle_flag = flag

    def set_resize_rect_type(self, resize_rect_type_=resize_rect_type.resize_XY):
        self.__resize_rect_type = resize_rect_type_

    def process(self):
        list_of_item = self.scene().items()
        list_of_rect = []
        list_of_ellipse = []
        for item in list_of_item:
            if (not (item is self.__m_outline_item)) and (not (item is self.__m_background_item)):
                if type(item) == my_rect_item:
                    list_of_rect.append(item)
                if type(item) == my_ellipse_item:
                    list_of_ellipse.append(item)

        self.__rect_pos = [(it.get_pos(), it.get_rect_size(), it.get_cnn_model(), it.get_signal_ref())
                           for it in list_of_rect]

        print(self.__rect_pos)

        if len(list_of_ellipse) == 4:
            pos0 = list_of_ellipse[0].get_pos()
            pos1 = list_of_ellipse[1].get_pos()
            pos2 = list_of_ellipse[2].get_pos()
            pos3 = list_of_ellipse[3].get_pos()

            angle_3vec = calculate_angle_3vec(pos0, pos1, pos2, pos3)
            max_angle = max(angle_3vec)
            if max_angle == angle_3vec[0]:
                # 0 1 2
                self.__lx, self.__ly, self.__sorted_pos = get_lx_ly_sorted_pos(pos0, pos1, pos2, pos3)
            elif max_angle == angle_3vec[1]:
                # 0 1 3
                self.__lx, self.__ly, self.__sorted_pos = get_lx_ly_sorted_pos(pos0, pos1, pos3, pos2)
            else:
                # 0 2 3
                self.__lx, self.__ly, self.__sorted_pos = get_lx_ly_sorted_pos(pos0, pos2, pos3, pos1)
            print('lx ly = ', self.__lx, ', ', self.__ly)
            pos_src = np.float32([self.__sorted_pos[0], self.__sorted_pos[1],
                                  self.__sorted_pos[2], self.__sorted_pos[3]])
            pos_dst = np.float32([[0, 0], [self.__lx, 0], [0, self.__ly], [self.__lx, self.__ly]])
            self.__perspective_transform_para = cv2.getPerspectiveTransform(pos_src, pos_dst)
            # img = cv2.imread(self.__file_name)
            dst = cv2.warpPerspective(self.__image, self.__perspective_transform_para, (int(self.__lx), int(self.__ly)))
            self.show_image(dst)
            cv2.imwrite('saved_img.jpg', dst)
            print(self)
            np.savez('PerspectiveTransform', sorted_pos=self.__sorted_pos,
                     lx=self.__lx, ly=self.__ly, rect_pos=self.__rect_pos)

    def __video(self):
        # success, frame = self.__vcap.read()
        # success, frame = self.__vcap.read()
        success, frame = self.__vcap.read()
        self.__detect_rect.clear()
        if success:
            if self.__mode == mode_type.select:
                pass
            elif self.__mode == mode_type.auto_select:
                class_ids, confidences, boxes = self.__ncs_net.detect(frame, confThreshold=0.5)
                for class_id, confidence, box in zip(list(class_ids), list(confidences), boxes):
                    if int(class_id[0]) < 8:
                        str_text = label[int(class_id[0])] + ': ' + format(confidence[0], '.2f')
                    else:
                        str_text = 'other: ' + format(confidence[0], '.2f')
                    cv2.putText(frame, str_text, (int(box[0]), int(box[1]+30)), cv2.FONT_HERSHEY_SIMPLEX, 1, (23, 230, 210), 2)
                    cv2.rectangle(frame, box, color=(0, 255, 0))
                    # self.place_rectangle(x=box[0], y=box[1], w_x=box[2], w_y=box[3])
                    self.__detect_rect.append(detect_rect(box, str_text))
                    # self.place_rectangle(x=0, y=0, w_x=60, w_y=60)
                    # if self.__first:
                    #     self.place_rectangle(x=572, y=403, w_x=60, w_y=60)
                    #     self.__first = False
                    # print('box = {} {} {} {}'.format(box[0], box[1], box[2], box[3]))
            elif self.__mode == mode_type.run:
                if self.__transform:
                    frame = cv2.warpPerspective(frame, self.__perspective_transform_para, (int(self.__lx), int(self.__ly)))
                for it in self.__rect_pos:
                    roi = frame[it[0][1]: (it[0][1] + it[1][1]), it[0][0]: (it[0][0] + it[1][0])]
                    if it[2] in "deng2":
                        self.__cnn_model_dict['deng2'].setInput(cv2.dnn.blobFromImage(roi, size=(40, 40), swapRB=False, crop=False))
                        img_class = self.__cnn_model_dict['deng2'].forward()
                        if img_class.shape[1] < 3:
                            return
                        if img_class[0][0] >= 0.8:
                            color = (0, 0, 255)
                            if not self.__class_result[it[3]] == '红':
                                self.__class_result[it[3]] = '红'
                                self.class_result_output.emit(it[3])
                        elif img_class[0][1] >= 0.8:
                            color = (0, 255, 0)
                            if not self.__class_result[it[3]] == '绿':
                                self.__class_result[it[3]] = '绿'
                                self.class_result_output.emit(it[3])
                        else:
                            color = (255, 0, 0)
                            if not self.__class_result[it[3]] == '不亮':
                                self.__class_result[it[3]] = '不亮'
                                self.class_result_output.emit(it[3])
                        cv2.rectangle(frame, it[0], (it[0][0] + it[1][0], it[0][1] + it[1][1]), color, 3)
                    elif it[2] in "kaiguan":
                        self.__cnn_model_dict['kaiguan'].setInput(cv2.dnn.blobFromImage(roi, size=(40, 40), swapRB=False, crop=False))
                        img_class = self.__cnn_model_dict['kaiguan'].forward()
                        if img_class.shape[1] < 2:
                            return
                        if img_class[0][0] >= 0.8:
                            color = (0, 0, 255)
                            if not self.__class_result[it[3]] == '合':
                                self.__class_result[it[3]] = '合'
                                self.class_result_output.emit(it[3])
                        else:
                            color = (0, 255, 0)
                            if not self.__class_result[it[3]] == '分':
                                self.__class_result[it[3]] = '分'
                                self.class_result_output.emit(it[3])
                        cv2.rectangle(frame, it[0], (it[0][0] + it[1][0], it[0][1] + it[1][1]), color, 3)

        if success:
            self.show_image(frame)

    def get_class_result_output(self):
        return self.__class_result

    def set_auto_select(self, en):
        if en:
            self.__mode = mode_type.auto_select
        else:
            self.__mode = mode_type.run
        self.__ncs_net = cv2.dnn_DetectionModel('ssd_mobile_v2/frozen_inference_graph.xml',
                                                'ssd_mobile_v2/frozen_inference_graph.bin')
        self.__ncs_net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)
        self.__ncs_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)

    def open_camera(self):
        camera_address = 0
        self.__mode = mode_type.run
        (text, bool_) = QtWidgets.QInputDialog.getText(None, "Set Camera Address", "default 0")
        if bool_:
            if not text in '':
                camera_address = text
        self.__class_result.clear()
        for it in self.__rect_pos:
            if len(it) == 4:
                self.__class_result[it[3]] = ''
        self.__vcap = cv2.VideoCapture(camera_address)
        self.__vcap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.__vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, 800)
        if not self.__vcap:
            print('Can not open camera!')
            return
        self.__video_timer.start(int(1000 / 10))
        print(self.__rect_pos)

    def set_parameters(self):
        self.__mode = mode_type.select
        self.__video_timer.stop()
        self.__vcap.release()

    def set_transform(self, state):
        self.__transform = state












        #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #print(gray.shape)
        #gray = cv2.medianBlur(gray, 5)
        #print(gray.shape)
        #gray = cv2.GaussianBlur(gray, (9, 9), 0)
        #print(gray.shape)
        #gray = cv2.Canny(gray, 10, 30)
        #print(gray.shape)

        #qimg = cv_common.cv_img2qimage(img)

    # def mouseMoveEvent(self, event: QtGui.QMouseEvent):
    #     if self.mDragWindow:
    #         #self.scrollContentsBy(100, 100)
    #         #QtWidgets.QGraphicsView.scroll(self, )
    #         self.horizontalScrollBar().scroll((event.globalPos() - self.mMousePoint).x(), (event.globalPos() - self.mMousePoint).y())
    #
    #         #self.scroll((event.globalPos() - self.mMousePoint).x(), (event.globalPos() - self.mMousePoint).y())
    #         print('dx=', (event.globalPos() - self.mMousePoint).x(), 'dy=', (event.globalPos() - self.mMousePoint).y())
    #         self.mMousePoint = event.globalPos()
    #         event.accept()
    #


    #
    # def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
    #     if event.button() == QtCore.Qt.RightButton:
    #         self.mDragWindow = False
    #         event.accept()
