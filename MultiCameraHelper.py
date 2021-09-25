from threading import Thread
from collections import deque
import time
import cv2
import imutils

def show_cams(cams):
    print ("Press 'q' to exit.")
    while True:
        for i, cam in enumerate(cams):
            frame = cam.get_frame()
            if frame is not None:
                cv2.imshow("Cam "+str(i), frame)

        if cv2.waitKey(1) & 0XFF == ord('q'):
            print ("'q' pressed! Exiting...")
            for cam in cams:
                cam.stop_thread = True
            cv2.destroyAllWindows()
            break

def process_camera_frames(cam):
    frame = cam.get_frame()
    if frame is not None:
        ## Implement Flow Here
        pass

class CameraHelper(object):
    def __init__(self, src_path, resize=True, height=None, width=None, retry_wait_minutes=1, deque_fps_seconds=10):
        self.src_path = src_path
        self.width = width
        self.height = height
        self.resize = False if self.width is None and self.height is None else resize
        self.retry_wait_minutes = retry_wait_minutes
        self.connected = False
        self.frame = None
        self.ret = False
        self.stream = None
        self.deque_fps_seconds = deque_fps_seconds
        self.deque = None
        self.stop_thread = False

        self.get_frame_thread = Thread(target=self.queue_frames, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

    def __del__(self):
        self.stream.release()

    def resize_frame(self):
        if self.resize:
            if self.width is not None and self.height is not None:
                self.frame = imutils.resize(self.frame, width=self.width, height=self.height)
            elif self.width is not None:
                self.frame = imutils.resize(self.frame, width=self.width)
            elif self.height is not None:
                self.frame = imutils.resize(self.frame, height=self.height)

    def connect(self):
        if self.connected:
            print ("Already connected!")
        else:
            while not self.connected:
                try:
                    error = None
                    self.stream = cv2.VideoCapture(self.src_path)
                    if self.stream.isOpened():
                        self.ret, self.frame = self.stream.read()
                        if not self.ret or self.frame is None:
                            print ("Connection Error Type 1! Retrying in {} second(s). ({})".format(int(self.retry_wait_minutes * 60), "Connection opened but unable to fetch frame!"))
                            time.sleep(int(self.retry_wait_minutes * 60))
                            continue
                        self.fps = self.stream.get(cv2.CAP_PROP_FPS)
                        self.deque = deque(maxlen=int(self.deque_fps_seconds*self.fps))
                        self.connected = True
                    else:
                        self.connected = False
                except Exception as ex:
                    error = str(ex)
                    self.connected = False
                finally:
                    if not self.connected:
                        print ("Connection Error Type 2! Retrying in {} second(s). ({})".format(int(self.retry_wait_minutes * 60), error))
                        time.sleep(int(self.retry_wait_minutes * 60))
                    else:
                        if self.width is None and self.height is None:
                            self.height, self.width = self.frame.shape[:2]
                        else:
                            self.resize_frame()
                            self.height, self.width = self.frame.shape[:2]
                        print ("Connected successfully established with: {}".format(self.src_path))
                        print ("FPS: {}".format(self.fps))
                        print ("Stream Resolution (Height, Width): ({}, {})".format(self.height, self.width))


    def queue_frames(self):
        time.sleep(5)
        self.connect()
        process_camera_frames(self)
        while not self.stop_thread:
            try:
                if self.stream:
                    self.ret, self.frame = self.stream.read()

                if self.stream.isOpened() and self.ret and self.frame is not None:
                    self.resize_frame()
                    self.deque.append(self.frame)
                else:
                    print ("Connection broke with camera feed: {}! Trying to re-connect...".format(self.src_path))
                    self.connected = False
                    self.connect()

            except Exception as e:
                print ("Exception: {}".format(str(e)))
        if self.stream:
            self.stream.release()
            self.stream = None
            self.connected=False
            self.frame = None
            self.ret = False

    def get_frame(self):
        if self.deque:
            frame = self.deque.pop()
            return frame
        else:
            return None

if __name__ == '__main__':
    cam1 = CameraHelper("http://213.193.89.202/mjpg/video.mjpg", height=600, width=800)
    cam2 = CameraHelper("rtsp://192.168.100.22:8080/h264_pcm.sdp", height=600, width=800)

    # FOR TESTING
    show_cams([cam1, cam2])
