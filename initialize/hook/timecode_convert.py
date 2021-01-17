
class TC_Op():
	def __init__(self, framerate):
		self.framerate = framerate

	def _seconds(self, value):
	    if isinstance(value, str):  # value seems to be a timestamp
	        _zip_ft = zip((3600, 60, 1, 1/self.framerate), value.split(':'))
	        return sum(f * float(t) for f,t in _zip_ft)
	    elif isinstance(value, (int, float)):  # frames
	        return value / self.framerate
	    else:
	        return 0

	def _timecode(self, seconds):
	    return '{h:02d}:{m:02d}:{s:02d}:{f:02d}' \
	            .format(h=int(seconds/3600),
	                    m=int(seconds/60%60),
	                    s=int(seconds%60),
	                    f=int(round((seconds-int(seconds))*self.framerate)))

	def _frames(self, seconds):
	    return seconds * self.framerate

	def timecode_to_frames(self, timecode, start=None):
	    return self._frames(self._seconds(timecode) - self._seconds(start))

	def frames_to_timecode(self, frames, start=None):
	    return self._timecode(self._seconds(frames) + self._seconds(start))





#print TC_Op(24).frames_to_timecode(1993512)

