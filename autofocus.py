#!/usr/bin/env python3
import os
import time
from datetime import datetime
import argparse
import csv
import cv2
import numpy as np

default_conf_file = './etc/focus.conf'

def focusing(val, channel=6, sleep=0.0):
        value = (val << 4) & 0x3ff0
        data1 = (value >> 8) & 0x3f
        data2 = value & 0xf0
        ret = os.system("i2cset -y %d 0x0c %d %d" % (channel, data1,data2))
        if sleep > 0.0:
            time.sleep(sleep)
        return ret

def save_image(img, basename, imgformat='png'):
    now = datetime.now()
    timestamp = now.strftime('_%Y-%m-%d_%H-%M-%S')
    filename = './' + basename + timestamp + '.' + imgformat
    print("save", filename)
    cv2.imwrite(filename, img)

def stopwatch():
    start_time = time.time()
    def print_wrap():
        nonlocal start_time
        return time.time() - start_time
    return print_wrap

class Ringbuffer(object):
    def __init__(self, size):
        self.buffer = [None] * size
        self.count = 0
        self.size = size
    def push(self, item):
        self.buffer[self.count % self.size] = item
        self.count += 1
    def getitems(self, recent=0):
        if recent <= 0:
            recent = self.size
        i = self.count % self.size
        if self.size > self.count:
            tmp = self.buffer[:i]
        else:
            tmp = self.buffer[i:] + (self.buffer[:i])
        return tmp[-recent:]

class Focuslist(Ringbuffer):
    def avg(self):
        items = self.getitems()
        ret = [j for i,j in items]
        if len(ret) == 0:
            return 0.0
        return sum(ret)/len(ret)
    def max(self):
        items = self.getitems()
        maxitem = (0,0.0)
        for i,j in items:
            if maxitem[1] <= j:
                maxitem = (i,j)
        return maxitem

def cliff_down_check(val, avg, atten_rate=0.03):
    if val >= avg * (1-atten_rate):
        return False
    else:
        return True

def laplacian(cap, times=3, ksize=3, window=False, save=False, crop_enable=False):
    # times の回数の平均をとる
    if save == True:
        times=1
    if times > 4:
        times = 3
    values = [0] * times
    for i in range(times):
        ret_val, img = cap.read()
        if window == True:
            cv2.imshow('CSI Camera', img)
        if crop_enable == True:
            img = crop(img)
        img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        img_sobel = cv2.Laplacian(img_gray,cv2.CV_32F,ksize=ksize)
        #img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U,ksize=ksize)
        img_sobel_abs = cv2.convertScaleAbs(src=img_sobel)
        if window == True:
            cv2.imshow('laplacian', img_sobel_abs)
        if save == True:
            save_image(img_sobel_abs, "edge")
        values[i] = cv2.mean(np.abs(img_sobel))[0]
        if window == True:
            cv2.waitKey(16) & 0xff
    return sum(values)/len(values)


def crop(src, crop_rate_h=0.3, crop_rate_w=0.5):
    src_height, src_width = src.shape[:2]
    h = int(src_height * crop_rate_h)
    w = int(src_width * crop_rate_w)
    y = int((src_height - h) / 2)
    x = int((src_width - w ) / 2)
    dst = src[y:y+h, x:x+w]
    return(dst)

def seek_focus(cap, start, stop, step, cap_times, buf_size=3, window=False):
    print(start, stop, step)
    timer = stopwatch()
    if start < 0:
        start = 0
    if stop > 1023:
        stop = 1024
    focus_buf = Focuslist(size=buf_size)
    cliff_down = False
    focusing(0, sleep=0.2)
    for i in range(start, stop+1, step):
        focusing(i, sleep=0.2)
        val = laplacian(cap, times=cap_times, window=window, crop_enable=True)
        print("%d,%.3f" % (i, val))
        cliff_down = cliff_down_check(val, focus_buf.avg())
        if cliff_down == True:
            break
        else:
            focus_buf.push((i,val))
    new_step = int(step/2)
    max_index, max_value = focus_buf.max()
    print("TIMES: %d, LAP: %.2f s" % (cap_times, timer()))
    if new_step > 1:
        new_stop=max_index + (step * 2)
        new_start=max_index - (step * 2)
        new_buf_size = int((new_stop - new_start)/new_step)
        max_index, max_value = seek_focus(cap, new_start, new_stop, new_step, cap_times+1, buf_size=new_buf_size, window=window)
    else:
        print("focal: %d, laplacian: %.4f" % (max_index, max_value))
        focusing(max_index)
    return(max_index, max_value)

def gstreamer_pipeline (capture_width=3264, capture_height=2464, display_width=3264, display_height=2464, framerate=21, flip_method=0) :
    return ('nvarguscamerasrc ! '
    'video/x-raw(memory:NVMM), '
    'width=(int)%d, height=(int)%d, '
    'format=(string)NV12, framerate=(fraction)%d/1 ! '
    'nvvidconv flip-method=%d ! '
    'video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! '
    'videoconvert ! '
    'video/x-raw, format=(string)BGR ! '
    'identity drop-allocation=1 ! appsink'  % (capture_width,capture_height,framerate,flip_method,display_width,display_height))

def focus_camera(camera_id, flip_method=2, saveImage=False):
    #print('wait for other gstreamer proccess')
    #time.sleep(5)
    cap = cv2.VideoCapture(camera_id)
    try:
        backend = cap.getBackendName()
    except:
        print('camera_id %d is not opened yet. open gstreamer' % camera_id )
        cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=flip_method), cv2.CAP_GSTREAMER)
    focal_distance = 0 # 焦点距離。最短0,最長1023の範囲
    focal_step = 10 # 焦点の変更step
    focal_stop = 500 # 300で10m-15mくらいなのでそこまでの範囲で探す
    cap_times = 1 # laplacianの実行回数
    if cap.isOpened():
        focusing(0)
        # wait for video sync
        for i in range(5):
            ret, img = cap.read()

        focal_distance, val = seek_focus(cap, focal_distance, focal_stop, focal_step, cap_times)

        if saveImage == True:
            # wait for video sync
            for i in range(20):
                ret, img = cap.read()
            ret, img = cap.read()
            save_image(img, 'raw')
            laplacian(cap, times=1, save=True)
        cap.release()
        return (focal_distance, val)
    else:
        print('Unable to open camera')
        return -1

def write_config(config_file, camera_id, focal_distance):
    with open(config_file, 'w') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['#camera_id','focal_distance'])
        csv_writer.writerow([camera_id,focal_distance])

def check_config(config_file):
    if not os.path.exists(config_file):
        return False
    with open(config_file, 'r') as f:
        rows = csv.reader(f)
        header = next(rows)
        for row in rows:
            camera_id, focal_distance = row
    if camera_id and int(focal_distance) > -1 and int(focal_distance) < 1024:
        return [int(camera_id), int(focal_distance)]
    else:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--set', type=int)
    parser.add_argument('--clear', action='store_true')
    parser.add_argument('--repeat', action='store_true')
    parser.add_argument('--save_image', action='store_true')
    parser.add_argument('--camera_id', type=int, default=1)
    parser.add_argument('--flip_method', type=int, default=2)
    parser.add_argument('--config_file', type=str, default=default_conf_file)
    arg = parser.parse_args()
    if arg.set:
        if arg.set < 1 or arg.set > 1023:
            print("range(0,1024) for forcusing")
            exit(1)
        result = focusing(arg.set)
        write_config(arg.config_file, arg.camera_id, arg.set)
        if result != 0:
            print('camera power is off, so just wrote new value to config')
    elif arg.repeat:
        f = open('results.txt', 'a')
        for i in range(0,20):
            (focal_distance, val) = focus_camera(arg.camera_id)
            f.write("COUNT: %d, DISTANCE: %d, VALUE: %.4f\n" % (i, focal_distance, val))
            f.flush()
        f.close()
    elif arg.clear:
        if os.path.exists(arg.config_file):
            os.remove(arg.config_file)
    else:
        ret = check_config(arg.config_file)
        if ret:
            result = focusing(ret[1])
            if result == 0:
                print('set focus to %d' % ret[1])
            else:
                print('not set focus, but config file exists, no problem.')
        else:
            (focal_distance,val) = focus_camera(arg.camera_id, arg.flip_method, arg.save_image)
            if focal_distance > -1:
                write_config(arg.config_file, arg.camera_id, focal_distance)

if __name__ == '__main__':
    main()
