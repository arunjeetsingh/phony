import threading
import time

from phony.base.log import ClassLogger

class Njm2670HbridgeRinger(ClassLogger):
  RING_FREQUENCY_HZ = 20
  RING_DURATION_SEC = 2.0
  PAUSE_DURATION_SEC = 2.0

  _outputs = None
  _polarity = 0

  _stop = None
  _thread = None
  _on_period = 0
  _off_period = 0
  _ring_duration = -1

  def __init__(self, io_outputs):
    ClassLogger.__init__(self)

    self._stop = threading.Event()

    self._outputs = io_outputs
    # De-energize hbridge
    self._outputs.ringer_enable(0)
    self._outputs.ringer_1(0)
    self._outputs.ringer_2(0)

  @ClassLogger.TraceAs.event()
  def short_ring(self):
    if not self.is_ringing():
      self._on_period = 0.20
      self._off_period = 0
      self._ring_duration = 0.20

      self._thread = threading.Thread(target = self.run)
      self._thread.start()

  @ClassLogger.TraceAs.event()
  def start_ringing(self):
    if not self.is_ringing():
      self._on_period = self.RING_DURATION_SEC
      self._off_period = self.PAUSE_DURATION_SEC
      self._ring_duration = -1

      self._thread = threading.Thread(target = self.run)
      self._thread.start()

  @ClassLogger.TraceAs.call()
  def stop_ringing(self):
    if self.is_ringing():
      self._stop.set()
      self._thread.join()
      self._stop.clear()

  def is_ringing(self):
    return self._thread != None and self._thread.is_alive()

  def run(self):
    ring_period_sec = 1.0 / self.RING_FREQUENCY_HZ

    self._ringer_enable(1)

    time_to_stop = time.time() + self._ring_duration
    while self._is_running() and (self._ring_duration < 0 or time.time() < time_to_stop):

      on_period = time.time() + self._on_period
      while self._is_running() and time.time() < on_period:
        self._ding()
        time.sleep(ring_period_sec)

      self._sleep_or_exit(self._off_period)

    self._ringer_enable(0)

  def _ringer_enable(self, value):
    self._outputs.ringer_enable(value)

  def _ding(self):
    self._outputs.ringer_1(self._polarity)
    self._polarity = not self._polarity
    self._outputs.ringer_2(self._polarity)

  def _sleep_or_exit(self, seconds):
    sleep_period = time.time() + seconds
    while self._is_running() and time.time() < sleep_period:
      time.sleep(0.001)

  def _is_running(self):
    return not self._stop.is_set()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.stop_ringing()