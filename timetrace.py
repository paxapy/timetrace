# coding:utf-8
import os
import sys
import imghdr
from itertools import chain as ch, ifilter as ifil

import cv2
import numpy

from PIL import ImageChops, Image
from PyQt4 import QtGui, QtCore


def handle_video(video_path, method='lighter', frame_count=0, full_path=False):
    dir_name = os.path.dirname(video_path)
    in_name, ext = os.path.splitext(os.path.basename(video_path))
    in_name = '{name}_{count}'.format(name=in_name, count=frame_count) if frame_count else in_name

    if method == 'both':
        lighter = handle_video(video_path, 'lighter', frame_count, full_path=True)
        darker = handle_video(video_path, 'darker', frame_count, full_path=True)
        l_img = Image.open(lighter)
        d_img = Image.open(darker)
        res = ImageChops.blend(l_img, d_img, 0.5)
        full_path, result_name = save_result(res, dir_name, in_name, method)
        return result_name

    out_name = '{in_name}_{method}_result.mov'.format(in_name=in_name, method=method)
    out_path = '{dir_name}/{out_name}'.format(dir_name=dir_name, out_name=out_name)
    cap = cv2.VideoCapture(video_path)
    count = 0
    while not cap.isOpened():
        cap = cv2.VideoCapture(video_path)
        cv2.waitKey(1000)
        print "Wait for the header"

    pos_frame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
    while True:
        flag, frame = cap.read()
        if flag:
            pos_frame = cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
            if count == 0:
                w, h = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
                out = cv2.VideoWriter(out_path, cv2.cv.CV_FOURCC(*'avc1'), 24, (w, h))
                count += 1
                prev = Image.fromarray(frame)
                continue
            if frame_count and count != 1 and count % frame_count:
                count += 1
                continue
            current = Image.fromarray(frame)
            if method == 'diff':
                diff = ImageChops.difference(current, prev)
                prev = current
                if count == 1:
                    finalimage = diff
                outframe = numpy.array(diff)
            else:
                if count == 1:
                    finalimage = current
                outframe = numpy.array(finalimage)
            if method == 'lighter':
                finalimage = ImageChops.lighter(finalimage, current)
            if method == 'darker':
                finalimage = ImageChops.darker(finalimage, current)
            out.write(outframe)
            cv2.imshow('video', outframe)
            count += 1
        else:
            cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, pos_frame - 1)
            print "frame is not ready"
            break
        if cv2.waitKey(10) == 27:
            break
        if cap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES) == cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT):
            break
    finalimage_data = cv2.cvtColor(numpy.array(finalimage), cv2.COLOR_RGB2BGR)
    finalimage = Image.fromarray(finalimage_data)
    path, result_name = save_result(finalimage, dir_name, in_name, method)
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    return path if full_path else result_name


def handle_photo(photo_path, method, frame_count=None, full_path=False):
    paths = ['{}/{}'.format(photo_path, file_path) for file_path in os.listdir(photo_path)]
    files = ['{}/{}'.format(p, f) for p in ifil(os.path.isdir, paths) for f in os.listdir(p)]
    files = list(ch(files, list(ifil(os.path.isfile, paths))))
    finalimage = None
    result_name = '{count}'.format(count=frame_count) if frame_count else ''

    for i, file_path in enumerate(files):
        what = imghdr.what(file_path)
        if what in [None, 'gif']:
            files.pop(i)
            continue
        currentimage = Image.open(file_path)
        if what in ['png']:
            try:
                bg = Image.new("RGB", currentimage.size, (255, 255, 255))
                bg.paste(currentimage, mask=currentimage)
                currentimage = bg
            except ValueError:
                pass
        if finalimage is None:
            finalimage = currentimage
            continue
        if frame_count and i != 1 and i % frame_count:
            continue
        if method == 'both':
            lighter = handle_photo(photo_path, 'lighter', frame_count, full_path=True)
            darker = handle_photo(photo_path, 'darker', frame_count, full_path=True)
            l_img = Image.open(lighter)
            d_img = Image.open(darker)
            res = ImageChops.blend(l_img, d_img, 0.5)
            path, name = save_result(res, photo_path, result_name, method)
            return name
        if method == 'diff':
            if i < 1:
                continue
            prev = Image.open(files[i - 1])
            diff = ImageChops.difference(currentimage, prev)
            finalimage = ImageChops.add(finalimage, diff)
        if method == 'lighter':
            finalimage = ImageChops.lighter(finalimage, currentimage)
        if method == 'darker':
            finalimage = ImageChops.darker(finalimage, currentimage)
    path, name = save_result(finalimage, photo_path, result_name, method)
    return path if full_path else name


def save_result(res, dir_name, in_name, method):
    result_name = "{in_name}_{method}_result.jpg".format(in_name=in_name, method=method)
    full_path = "{dir_name}/{result_name}".format(dir_name=dir_name, result_name=result_name)
    res.save(full_path, quality=100)
    return full_path, result_name


class TimeTrace(QtGui.QWidget):

    def __init__(self):
        super(TimeTrace, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('TimeTrace 1.5')
        self.centralwidget = QtGui.QWidget(self)
        self.setGeometry(300, 300, 320, 250)
        self.frame_count = QtGui.QLineEdit(self.centralwidget)
        self.frame_count.setGeometry(QtCore.QRect(30, 20, 71, 21))
        self.frame_label = QtGui.QLabel('use every frame', self.centralwidget)
        self.frame_label.setGeometry(QtCore.QRect(110, 20, 141, 21))
        self.method = QtGui.QGroupBox('method', self.centralwidget)
        self.method.setGeometry(QtCore.QRect(30, 50, 120, 120))
        self.lighter = QtGui.QRadioButton('light', self.method)
        self.lighter.setGeometry(QtCore.QRect(0, 30, 101, 20))
        self.darker = QtGui.QRadioButton('dark', self.method)
        self.darker.setGeometry(QtCore.QRect(0, 50, 101, 20))
        self.both = QtGui.QRadioButton('both', self.method)
        self.both.setGeometry(QtCore.QRect(0, 70, 101, 20))
        self.diff = QtGui.QRadioButton('difference', self.method)
        self.diff.setGeometry(QtCore.QRect(0, 90, 101, 20))
        self.lighter.setChecked(True)
        self.video = QtGui.QPushButton('Video', self.centralwidget)
        self.video.setGeometry(QtCore.QRect(30, 180, 88, 27))
        self.photos = QtGui.QPushButton('Photo', self.centralwidget)
        self.photos.setGeometry(QtCore.QRect(120, 180, 88, 27))
        self.cancel = QtGui.QPushButton('Cancel', self.centralwidget)
        self.cancel.setGeometry(QtCore.QRect(210, 180, 88, 27))
        self.video.clicked.connect(self.video_select)
        self.photos.clicked.connect(self.photos_select)
        self.cancel.clicked.connect(self.exit)

        self.show()

    def get_method(self):
        method_map = {
            'diff': self.diff,
            'lighter': self.lighter,
            'darker': self.darker,
            'both': self.both
        }
        method = 'lighter'
        for m, w in method_map.items():
            if w.isChecked():
                method = m
        return method

    def video_select(self):
        vid_path = QtGui.QFileDialog.getOpenFileName(self, "Choose video")
        if vid_path:
            method = self.get_method()
            name = handle_video(str(vid_path), method, int(self.frame_count.text() or 0))
            QtGui.QMessageBox.about(self, "Done!", "Result is {name}".format(name=name))

    def photos_select(self):
        photos_path = QtGui.QFileDialog.getExistingDirectory(self, "Choose folder with photos")
        if photos_path:
            method = self.get_method()
            name = handle_photo(str(photos_path), method, int(self.frame_count.text() or 0))
            QtGui.QMessageBox.about(self, "Done!", "Result is in the same folder ({name})".format(name=name))

    def exit(self):
        sys.exit()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = TimeTrace()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
