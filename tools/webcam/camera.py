import av
import cv2 as cv

class Camera:
  def __init__(self, cam_type_state, stream_type, camera_id):
    try:
      camera_id = int(camera_id)
      use_v4l2 = True
    except ValueError: # allow strings, ex: /dev/video0
      use_v4l2 = False

    self.cam_type_state = cam_type_state
    self.stream_type = stream_type
    self.cur_frame_id = 0

    print(f"Opening {cam_type_state} at {camera_id}")

    if use_v4l2:
      self.cap = cv.VideoCapture(camera_id, cv.CAP_V4L2)
    else:
      self.cap = cv.VideoCapture(camera_id)

    # Use MJPEG for better WSL compatibility
    self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M','J','P','G'))
    self.cap.set(cv.CAP_PROP_BUFFERSIZE, 1)

    # Set resolution
    self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280.0)
    self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720.0)
    self.cap.set(cv.CAP_PROP_FPS, 25.0)

    self.W = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
    self.H = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)

    print(f"Camera initialized: {int(self.W)}x{int(self.H)}")
    print(f"Camera is opened: {self.cap.isOpened()}")

  @classmethod
  def bgr2nv12(self, bgr):
    frame = av.VideoFrame.from_ndarray(bgr, format='bgr24')
    return frame.reformat(format='nv12').to_ndarray()

  def read_frames(self):
    print(f"Starting to read frames from {self.cam_type_state}")
    retry_count = 0
    max_retries = 10
    frame_count = 0
    while True:
      ret, frame = self.cap.read()
      if not ret:
        retry_count += 1
        print(f"Failed to read frame, retry {retry_count}/{max_retries}")
        if retry_count >= max_retries:
          print("Max retries reached, camera may be disconnected")
          break
        continue

      retry_count = 0  # Reset on successful read
      frame_count += 1
      if frame_count % 20 == 0:  # Print every 20 frames
        print(f"Read {frame_count} frames successfully")

      # Rotate the frame 180 degrees (flip both axes)
      # frame = cv.flip(frame, -1)
      yuv = Camera.bgr2nv12(frame)
      yield yuv.data.tobytes()
    self.cap.release()
