import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer, pyqtSlot
from mainwindow import Ui_MainWindow
from GraphicsView import resize_rect_type
from PyQt5 import QtWidgets
import time
import tracemalloc


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.showMaximized()
        self.ui.actionNative.setChecked(True)
        self.ui.actionSet_Parameters.setChecked(True)
        self.ui.actionOpen_Camera.setChecked(False)
        self.ui.graphicsView.set_render(self.ui.graphicsView.RenderType.Native)
        self.ui.actionBackground.setChecked(True)
        self.ui.graphicsView.set_view_background(True)
        self.ui.actionOutline.setChecked(True)
        self.ui.actionresize_x_y.setChecked(True)
        self.ui.actionresize_x.setChecked(False)
        self.ui.actionresize_y.setChecked(False)
        self.ui.actionplace_rectangle.setChecked(False)
        self.ui.actionPlace_ellipse.setChecked(False)
        self.ui.actionedit_rectangle.setChecked(True)
        self.ui.actionErase_rectangle.setChecked(False)
        self.ui.graphicsView.set_view_outline(True)
        self.ui.actionAbout_QT.triggered.connect(self.__about_qt)
        self.ui.actionexit.triggered.connect(self.__exit_app)
        self.ui.actionopen.triggered.connect(self.__open_file)
        self.ui.actionNative.triggered.connect(self.__render_native)
        self.ui.actionOpenGL.triggered.connect(self.__render_openGL)
        self.ui.actionImage.triggered.connect(self.__render_image)
        self.ui.actionBackground.triggered.connect(self.__view_background)
        self.ui.actionOutline.triggered.connect(self.__view_outline)
        self.ui.actionzoom_in_canvas.triggered.connect(self.__zoom_in_canvas)
        self.ui.actionzoom_out_canvas.triggered.connect(self.__zoom_out_canvas)
        self.ui.actionplace_rectangle.triggered.connect(self.__place_rectangle)
        self.ui.actionPlace_ellipse.triggered.connect(self.__place_ellipse)
        self.ui.actionedit_rectangle.triggered.connect(self.__edit_rectangle)
        self.ui.actionErase_rectangle.triggered.connect(self.__remove_rectangle)
        self.ui.actionresize_x_y.triggered.connect(self.__resize_XY)
        self.ui.actionresize_x.triggered.connect(self.__resize_X)
        self.ui.actionresize_y.triggered.connect(self.__resize_Y)
        self.ui.actionProcess.triggered.connect(self.__process)
        self.ui.actionOpen_Camera.triggered.connect(self.__open_camera)
        self.ui.actionSet_Parameters.triggered.connect(self.__set_parameters)
        self.ui.graphicsView.class_result_output.connect(self.__refresh_class_result)
        self.ui.actiontransform.triggered.connect(self.__set_transform)
        self.ui.actionabout.triggered.connect(self.__about)
        self.ui.actionAuto_Select_Object.triggered.connect(self.__auto_select_object)

        self.__signal_table_model = self.__load_data(self)
        # 信号与槽的连接，这里是QStandardItemModel对象中的itemChanged信号，作用是如果
        # model中的数据如果发生改变，便会发送这个信号，同时会传递一个类型为QStandardItem的对象。槽为上面自定义的函数。
        # self.__signal_table_model.itemChanged.connect(self.__deal)
        self.ui.tableView_signal.setModel(self.__signal_table_model)

    @staticmethod
    def __about_qt():
        QApplication.instance().aboutQt()

    def __about(self):
        about = QtWidgets.QMessageBox.about(self, 'about', 'Version 0.1 \n Copyright © Gridnt. Inc')

    @staticmethod
    def __exit_app():
        QApplication.instance().closeAllWindows()

    def __view_background(self):
        self.ui.graphicsView.set_view_background(self.ui.actionBackground.isChecked())

    def __view_outline(self):
        self.ui.graphicsView.set_view_outline(self.ui.actionOutline.isChecked())

    def __render_native(self):
        self.ui.actionImage.setChecked(False)
        self.ui.actionOpenGL.setChecked(False)
        self.ui.actionNative.setChecked(True)
        self.ui.graphicsView.set_render(self.ui.graphicsView.RenderType.Native)

    def __render_openGL(self):
        self.ui.actionImage.setChecked(False)
        self.ui.actionOpenGL.setChecked(True)
        self.ui.actionNative.setChecked(False)
        self.ui.graphicsView.set_render(self.ui.graphicsView.RenderType.OpenGL)

    def __render_image(self):
        self.ui.actionImage.setChecked(True)
        self.ui.actionNative.setChecked(False)
        self.ui.actionOpenGL.setChecked(False)
        self.ui.graphicsView.set_render(self.ui.graphicsView.RenderType.Image)

    def __open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setViewMode(QFileDialog.List)
        file_dialog.setMimeTypeFilters(["image/jpeg", "image/png", "image/bmp", "image/svg+xml",
                                        "image/svg+xml-compressed", "application/octet-stream"])
        file_dialog.setWindowTitle("Open image")

        while file_dialog.exec() == QDialog.Accepted:
            break

        self.ui.graphicsView.open_file(file_dialog.selectedFiles()[0])
        print(file_dialog.selectedFiles()[0])

    def __zoom_in_canvas(self):
        self.ui.graphicsView.zoom_canvas(1.1)

    def __zoom_out_canvas(self):
        self.ui.graphicsView.zoom_canvas(0.9)

    def __place_rectangle(self):
        self.ui.actionplace_rectangle.setChecked(True)
        self.ui.actionPlace_ellipse.setChecked(False)
        self.ui.actionedit_rectangle.setChecked(False)
        self.ui.actionErase_rectangle.setChecked(False)
        self.ui.graphicsView.set_place_rectangle(True)
        self.ui.graphicsView.set_place_ellipse(False)
        self.ui.graphicsView.set_remove_rectangle(False)

    def __place_ellipse(self):
        self.ui.actionplace_rectangle.setChecked(False)
        self.ui.actionPlace_ellipse.setChecked(True)
        self.ui.actionedit_rectangle.setChecked(False)
        self.ui.actionErase_rectangle.setChecked(False)
        self.ui.graphicsView.set_place_rectangle(False)
        self.ui.graphicsView.set_place_ellipse(True)
        self.ui.graphicsView.set_remove_rectangle(False)

    def __edit_rectangle(self):
        self.ui.actionplace_rectangle.setChecked(False)
        self.ui.actionPlace_ellipse.setChecked(False)
        self.ui.actionedit_rectangle.setChecked(True)
        self.ui.actionErase_rectangle.setChecked(False)
        self.ui.graphicsView.set_place_rectangle(False)
        self.ui.graphicsView.set_place_ellipse(False)
        self.ui.graphicsView.set_remove_rectangle(False)

    def __remove_rectangle(self):
        self.ui.actionplace_rectangle.setChecked(False)
        self.ui.actionPlace_ellipse.setChecked(False)
        self.ui.actionedit_rectangle.setChecked(False)
        self.ui.actionErase_rectangle.setChecked(True)
        self.ui.graphicsView.set_place_rectangle(False)
        self.ui.graphicsView.set_place_ellipse(False)
        self.ui.graphicsView.set_remove_rectangle(True)

    def __resize_XY(self):
        self.ui.actionresize_x_y.setChecked(True)
        self.ui.actionresize_x.setChecked(False)
        self.ui.actionresize_y.setChecked(False)
        self.ui.graphicsView.set_resize_rect_type(resize_rect_type.resize_XY)

    def __resize_X(self):
        self.ui.actionresize_x_y.setChecked(False)
        self.ui.actionresize_x.setChecked(True)
        self.ui.actionresize_y.setChecked(False)
        self.ui.graphicsView.set_resize_rect_type(resize_rect_type.resize_X)

    def __resize_Y(self):
        self.ui.actionresize_x_y.setChecked(False)
        self.ui.actionresize_x.setChecked(False)
        self.ui.actionresize_y.setChecked(True)
        self.ui.graphicsView.set_resize_rect_type(resize_rect_type.resize_Y)

    def __process(self):
        self.ui.graphicsView.process()

    def __open_camera(self):
        self.ui.actionOpen_Camera.setChecked(True)
        self.ui.actionSet_Parameters.setChecked(False)
        self.ui.actionProcess.setEnabled(False)
        self.ui.actionresize_x.setEnabled(False)
        self.ui.actionresize_x_y.setEnabled(False)
        self.ui.actionresize_y.setEnabled(False)
        self.ui.actionplace_rectangle.setEnabled(False)
        self.ui.actionPlace_ellipse.setEnabled(False)
        self.ui.actionedit_rectangle.setEnabled(False)
        self.ui.actionErase_rectangle.setEnabled(False)
        self.ui.graphicsView.open_camera()

    def __auto_select_object(self):
        self.ui.graphicsView.set_auto_select(self.ui.actionAuto_Select_Object.isChecked())

    def __set_parameters(self):
        self.ui.actionOpen_Camera.setChecked(False)
        self.ui.actionAuto_Select_Object.setChecked(False)
        self.ui.actionSet_Parameters.setChecked(True)
        self.ui.actionProcess.setEnabled(True)
        self.ui.actionresize_x.setEnabled(True)
        self.ui.actionresize_x_y.setEnabled(True)
        self.ui.actionresize_y.setEnabled(True)
        self.ui.actionplace_rectangle.setEnabled(True)
        self.ui.actionPlace_ellipse.setEnabled(True)
        self.ui.actionedit_rectangle.setEnabled(True)
        self.ui.actionErase_rectangle.setEnabled(True)
        self.ui.graphicsView.set_parameters()

    def __set_transform(self):
        self.ui.graphicsView.set_transform(self.ui.actiontransform.isChecked())

    @pyqtSlot(str)
    def __refresh_class_result(self, res):
        class_result = self.ui.graphicsView.get_class_result_output()
        if not class_result[res] == '':
            row = self.__signal_table_model.rowCount()
            self.__signal_table_model.setItem(row, 0, QStandardItem(res))
            self.__signal_table_model.setItem(row, 1, QStandardItem(class_result[res]))
            self.__signal_table_model.setItem(row, 2, QStandardItem(str(time.ctime(time.time()))))

    @staticmethod
    def __load_data(self):
        # 生成一个模型，用来给tableview
        model = QStandardItemModel()
        # 打开一个csv文件
        # file = csv.reader(open(u'/Users/wzh/pythonfile/pachong/全国人口变化.csv', 'r'))
        # 取出csv文件的头部，类型为list，赋值给headdata
        # headdata = next(file)
        # 从headdata中取出数据，放入到模型中
        head_data = ['ref', 'signal', 'time']
        for i in range(len(head_data)):
            item = QStandardItem(head_data[i])
            # 设置模型的水平头部
            model.setHorizontalHeaderItem(i, item)
        #rown = 0
        # 从csv文件中取出数据，放入到模型中
        #for data in file:
        #    for coln in range(len(data)):
        #        item = QtGui.QStandardItem(data[coln])
                # 在模型的指定位置添加数据(item)
        #        model.setItem(rown, coln, item)
        #    rown += 1
        return model

    # 自定义槽函数，接收一个参数，类型为QStandardItem对象
    @pyqtSlot(QStandardItem)
    def __deal(self, item):
        print(u'位置(row,col):' + str(item.row()) + ',' + str(item.column()))
        print(u'改变了值')
        print(u'新值为:', item.text())


if __name__ == "__main__":
    # tracemalloc.start()

    app = QApplication(sys.argv)
    print(QtWidgets.QStyleFactory.keys())
    # app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

    window = MainWindow()
    window.show()
    # snapshot1 = tracemalloc.take_snapshot()
    # top_stats = snapshot1.statistics('lineno')  # 快照对象的统计
    # for stat in top_stats:
    #     print(stat)
    sys.exit(app.exec_())

