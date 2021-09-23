import cv2
import time
import imutils

class Camera(object):
    def __init__(self, src_path, resize=True, height=None, width=None, connect=True, retry_wait_minutes=1):
        self.src_path = src_path
        self.width = width
        self.height = height
        self.resize = False if self.width is None and self.height is None else resize
        self.retry_wait_minutes = retry_wait_minutes
        self.connected = False
        self.frame = None
        self.ret = False
        self.stream = None

        if connect:
            self.connect()

    def __del__(self):
        self.stream.release()
        cv2.destroyAllWindows()

    def resize_frame(self):
        if self.resize:
            if self.width is not None and self.height is not None:
                self.frame = imutils.resize(self.frame, width=self.width, height=self.height)
            elif self.width is not None:
                self.frame = imutils.resize(self.frame, width=self.width)
            elif self.height is not None:
                self.frame = imutils.resize(self.frame, height=self.height)


    def stop(self):
        self.connected = False
        self.stream.release()
        cv2.destroyAllWindows()
        
    def connect(self):
        if self.connected:
            print ("Already connected!")
        else:
            while not self.connected:
                try:
                    self.stream = cv2.VideoCapture(self.src_path)
                    if self.stream.isOpened():
                        self.ret, self.frame = self.stream.read()
                        if not self.ret or self.frame is None:
                            print ("Connection Error! Retrying in {} minute(s). ({})".format(self.retry_wait_minutes, "Connection opened but unable to fetch frame!"))
                            time.sleep(self.retry_wait_minutes * 60)
                            continue
                        self.fps = self.stream.get(cv2.CAP_PROP_FPS)
                        self.connected = True
                    else:
                        self.connected = False
                    error = None
                except Exception as ex:
                    error = str(ex)
                    self.connected = False
                finally:
                    if not self.connected:
                        print ("Connection Error! Retrying in {} minute(s). ({})".format(self.retry_wait_minutes, error))
                        time.sleep(self.retry_wait_minutes * 60)
                    else:
                        if self.width is None and self.height is None:
                            self.height, self.width = self.frame.shape[:2]
                        else:
                            self.resize_frame()
                            self.height, self.width = self.frame.shape[:2]
                        print ("Connected successfully established with: {}".format(self.src_path))
                        print ("FPS: {}".format(self.fps))
                        print ("Stream Resolution (Height, Width): ({}, {})".format(self.height, self.width))

    def read(self):
        try:
            if not self.connected:
                print ("Connection isn't established with the camera!")
                return False, None

            self.ret, self.frame = self.stream.read()
            if not self.ret or self.frame is None:
                print ("Connection isn't established with the camera! Trying to connect...")
                self.connected = False
                self.connect()

            self.resize_frame()
            return self.ret, self.frame
        except:
            return self.ret, self.frame


if __name__ == '__main__':
    path = "YOUR_CAM/VIDEO_PATH"
    cam = Camera(path, width=800)
    while True:
        ret, frame = cam.read()
        if ret:
            cv2.imshow('Frames', frame)
            key = cv2.waitKey(1)
            if key == ord('q'):
                cam.stop()
                break
