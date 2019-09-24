import typing
from timecode import Timecode


class Timecode:
    FRAMERATE = 29.97
    INT_FRAMERATE = 30

    def __init__(self, frame: int):
        self._frame = frame
        self._framerate = Timecode.FRAMERATE

    @classmethod
    def from_str(cls, timecode: str, df: bool = None) -> Timecode:
        if df is None:
            df = (timecode.find(';', ) >= 0)
        return cls(Timecode.tc_to_f(timecode, df))

    @property
    def frame(self) -> int:
        return self._frame

    @property
    def timecode(self, df=True) -> tuple:
        return Timecode.f_to_tc(self._frame, self._framerate, df)

    @property
    def ndf_timecode(self) -> tuple:
        return Timecode.f_to_tc(self._frame, self._framerate, False)

    @property
    def df_timecode(self) -> tuple:
        return Timecode.f_to_tc(self._frame, self._framerate, True)

    def to_seconds(self) -> int:
        hours, minutes, seconds, smpte_token, frames = self.timecode
        return (hours * 60 * 60) + (minutes * 60) + seconds

    def __str__(self):
        if self._framerate in [29.97, 59.94]:
            return "%02d:%02d:%02d%s%02d" % self.df_timecode
        else:
            return "%02d:%02d:%02d%s%02d" % self.ndf_timecode

    def __int__(self):
        return self._frame

    def __lt__(self, other):
        return self._frame < other.frame

    def __le__(self, other):
        return self._frame <= other.frame

    def __ge__(self, other):
        return self._frame >= other.frame

    def __eq__(self, other):
        return self._frame == other.frame

    def __ne__(self, other):
        return not (self._frame == other.frame)

    def __sub__(self, other):
        return Timecode(self._frame - other.frame)

    def __add__(self, other):
        return Timecode(self._frame + other.frame)

    @staticmethod
    def f_to_tc(total_frames: int, frame_rate: float, df: bool) -> tuple:
        """
        Method that converts frames to SMPTE timecode.

        :param total_frames: Number of frames
        :param frame_rate: frames per second
        :param df: true if time code should drop frames, false if not
        :returns: SMPTE timecode as string, e.g. '01:02:12:32' or '01:02:12;32'
        """
        if df and frame_rate not in [29.97, 59.94]:
            raise NotImplementedError("Time code calculation logic only supports drop frame "
                                      "calculations for 29.97 and 59.94 fps.")

        # for a good discussion around time codes and sample code, see
        # http://andrewduncan.net/timecodes/

        # round fps to the nearest integer
        # note that for frame rates such as 29.97 or 59.94,
        # we treat them as 30 and 60 when converting to time code
        # then, in some cases we 'compensate' by adding 'drop frames',
        # e.g. jump in the time code at certain points to make sure that
        # the time code calculations are roughly right.
        #
        # for a good explanation, see
        # https://documentation.apple.com/en/finalcutpro/usermanual/index.html#chapter=D%26section=6
        fps_int = int(round(frame_rate))

        if df:
            df_frames = total_frames
            # drop-frame-mode
            # add two 'fake' frames every minute but not every 10 minutes
            #
            # example at the one minute mark:
            #
            # frame: 1795 non-drop: 00:00:59:25 drop: 00:00:59;25
            # frame: 1796 non-drop: 00:00:59:26 drop: 00:00:59;26
            # frame: 1797 non-drop: 00:00:59:27 drop: 00:00:59;27
            # frame: 1798 non-drop: 00:00:59:28 drop: 00:00:59;28
            # frame: 1799 non-drop: 00:00:59:29 drop: 00:00:59;29
            # frame: 1800 non-drop: 00:01:00:00 drop: 00:01:00;02
            # frame: 1801 non-drop: 00:01:00:01 drop: 00:01:00;03
            # frame: 1802 non-drop: 00:01:00:02 drop: 00:01:00;04
            # frame: 1803 non-drop: 00:01:00:03 drop: 00:01:00;05
            # frame: 1804 non-drop: 00:01:00:04 drop: 00:01:00;06
            # frame: 1805 non-drop: 00:01:00:05 drop: 00:01:00;07
            #
            # example at the ten minute mark:
            #
            # frame: 17977 non-drop: 00:09:59:07 drop: 00:09:59;25
            # frame: 17978 non-drop: 00:09:59:08 drop: 00:09:59;26
            # frame: 17979 non-drop: 00:09:59:09 drop: 00:09:59;27
            # frame: 17980 non-drop: 00:09:59:10 drop: 00:09:59;28
            # frame: 17981 non-drop: 00:09:59:11 drop: 00:09:59;29
            # frame: 17982 non-drop: 00:09:59:12 drop: 00:10:00;00
            # frame: 17983 non-drop: 00:09:59:13 drop: 00:10:00;01
            # frame: 17984 non-drop: 00:09:59:14 drop: 00:10:00;02
            # frame: 17985 non-drop: 00:09:59:15 drop: 00:10:00;03
            # frame: 17986 non-drop: 00:09:59:16 drop: 00:10:00;04
            # frame: 17987 non-drop: 00:09:59:17 drop: 00:10:00;05

            # calculate number of drop frames for a 29.97 std NTSC
            # workflow. Here there are 30*60 = 1800 frames in one
            # minute

            FRAMES_IN_ONE_MINUTE = 1800 - 2

            FRAMES_IN_TEN_MINUTES = (FRAMES_IN_ONE_MINUTE * 10) - 2

            ten_minute_chunks = df_frames / FRAMES_IN_TEN_MINUTES
            one_minute_chunks = df_frames % FRAMES_IN_TEN_MINUTES

            ten_minute_part = 18 * ten_minute_chunks
            one_minute_part = 2 * ((one_minute_chunks - 2) / FRAMES_IN_ONE_MINUTE)

            if one_minute_part < 0:
                one_minute_part = 0

            # add extra frames
            df_frames += ten_minute_part + one_minute_part

            # for 60 fps drop frame calculations, we add twice the number of frames
            if fps_int == 60:
                df_frames = df_frames * 2

            # time codes are on the form 12:12:12;12
            smpte_token = ";"

            total_frames = df_frames
        else:
            # time codes are on the form 12:12:12:12
            smpte_token = ":"

        # now split our frames into time code
        hours = int(total_frames / (3600 * fps_int))
        minutes = int(total_frames / (60 * fps_int) % 60)
        seconds = int(total_frames / fps_int % 60)
        frames = int(total_frames % fps_int)

        return hours, minutes, seconds, smpte_token, frames

    @staticmethod
    def tc_to_f(timecode_str: str, df=False) -> int:
        if timecode_str.startswith('--:--:--'):
            return 0

        if df:
            return Timecode.df_to_f(timecode_str)
        else:
            return Timecode.ndf_to_f(timecode_str)

    @staticmethod
    def ndf_to_f(timecode_str: str) -> int:
        hours, minutes, seconds, *_ = timecode_str.split(':')
        try:
            frames = timecode_str.split(':', 3)[3]
        except (ValueError, IndexError):
            frames = 0

        frame_number = int(frames)
        frame_number += int(seconds) * 30
        frame_number += int(minutes) * 60 * 30
        frame_number += int(hours) * 60 * 60 * 30
        return frame_number

    @staticmethod
    def df_to_f(timecode_str: str) -> int:
        # see https://github.com/eoyilmaz/timecode/blob/master/timecode/__init__.py
        hours, minutes, seconds = map(int, timecode_str.split(':'))
        try:
            frames = timecode_str.split(';', 2)[1]
        except (ValueError, IndexError):
            frames = 0

        ffps = float(Timecode.FRAMERATE)
        drop_frames = int(round(ffps * 0.06666666))
        ifps = Timecode.INT_FRAMERATE
        hour_frames = ifps * 60 * 60
        minute_frames = ifps * 60
        total_minutes = (60 * hours) + minutes

        frame_number = \
            ((hour_frames * hours)
             + (minute_frames * minutes)
             + (ifps * seconds) + frames) \
             - (drop_frames * (total_minutes - (total_minutes // 10)))

        return int(frame_number + 1)

# # usage example
# frames = Timecode.timecode_to_frames(sys.argv[1])
# tc = Timecode.frames_to_timecode(frames, 29.97, True)
# #
# print(sys.argv[1], frames, tc)
