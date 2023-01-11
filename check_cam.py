#!/usr/bin/env python3
import sys
import os
import cv2
from autofocus import focusing, laplacian

focal_start = 100
focal_stop  = 300
focal_step  = 5
buffer_size = 5
def check_argv():
    if len(sys.argv) > 1:
        camname = "%05d" % int(sys.argv[1])
    else:
        camname = input_cam()
    return camname

def mksavedir(camname):
    save_dir = 'check/' + camname +"/"
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def input_cam(count=0):
    val = input("input camera serial number: ")
    try:
        return "%05d" % int(val)
    except ValueError:
        print("Plese cam number in NUMERICS")
        if count > 2:
            print("You input wrong values in many times. exit")
            sys.exit(1)
        count += 1
        return input_cam(count)

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

def main():
    camname = check_argv()
    save_basename = "./Check/" + camname
    logfile = save_basename + "_log.csv"
    imgfile = save_basename + "_raw.png"
    focalfile = save_basename + "_focal.txt"

    log_f = open(logfile, "w")
    focal_f = open(focalfile, "w")
    cap = cv2.VideoCapture(1)
    #cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap_focus = cv2.VideoCapture(3)
    #cap_focus.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    focus_buf = Focuslist(size=buffer_size)
    cliff_down = False

    for i in range(focal_start,focal_stop+1,focal_step):
        focusing(i, sleep=0.2)
        #val = laplacian(cap, ksize=3, crop_enable=True)
        val = laplacian(cap_focus, times=2, ksize=3)
        #val = laplacian(cap, ksize=3)
        cliff_down = cliff_down_check(val, focus_buf.avg())
        if not cliff_down:
            #print("PUSH: %d" % i)
            focus_buf.push((i,val))

        print("%d,%.3f" % (i,val))
        log_f.write("%d,%.3f\n" % (i,val))
        log_f.flush()
    log_f.close()
    if not cliff_down:
        print("CLIFF DOWN NOT DETECTED!!")
        focal_f.write("CLIFF DOWN NOT DETECTED!!\n")
        focal_f.close()
        sys.exit(1)
    focal_distance,max_value = focus_buf.max()
    print("focal_distance = %d" % focal_distance)

    focusing(focal_distance, sleep=0.2)
    # wait for video sync
    for i in range(3):
        ret, img_croped = cap.read()
    ret, img = cap.read()
    cv2.imwrite(imgfile, img)
    focal_f.write("%d,%.3f\n" % (focal_distance,max_value))
    focal_f.close()


if __name__ == "__main__":
    main()
