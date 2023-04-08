import os
import pyaudio
import numpy as np
import time
import urllib.request
import slackweb
from scipy.signal import argrelmax

# setting
CHUNK = 1024
RATE = 8000  # サンプリング周波数
#ALARM_FREQ = 2000  # アラーム音の周波数 Toshiba TW130VB
ALARM_FREQ = 1950  # アラーム音の周波数 Panasonic NA-LX113B
FREQ_COUNT = 3  # 最大音量の周波数カウント数
PEAK_COUNT = 0
LOOP_MAX = 100  # 誤検知回避のためカウント回数リセット
dt = 1/RATE
freq = np.linspace(0, 1.0/dt, CHUNK)
detect_freq = []
MARGIN = 10  # 周波数のマージン Hz
ALEXA_URL = 'http://10.0.1.6:1880/sentakuki/'  # Alexa通知サーバurl

#BEEP_DURATION = 0.5  # ビープ音の持続時間 (秒)
BEEP_DURATION = 0.4  # ビープ音の持続時間 (秒)
#BEEP_INTERVAL = 0.7  # ビープ音の間隔 (秒)
BEEP_INTERVAL = 0.6  # ビープ音の間隔 (秒)
BEEP_REPEAT_COUNT = 6  # ビープ音の繰り返し回数

beep_detected_count = 0
silence_detected_count = 0
in_beep = False
in_silence = False
alarm_time = time.time()


def timeRecord():
    alarm_time = time.time()

def slack():
    text = "洗濯機アラーム検知"
    slack = slackweb.Slack(url="https://hooks.slack.com/services/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")
    slack.notify(text = text, channel="#private-fuka-ch", username="sentakuki-beep", icon_emoji=":raspberrypi:", mrkdwn=True)


def getMaxFreqFFT(sound, chunk, freq):
    f = np.fft.fft(sound) / (chunk / 2)
    f_abs = np.abs(f)

    peak_args = argrelmax(f_abs[:(int)(chunk / 2)], order=8)
    f_peak = f_abs[peak_args]
    f_peak_argsort = f_peak.argsort()[::-1]
    peak_args_sort = peak_args[0][f_peak_argsort]

    i = 0
    PEAK_FLAG = 0

    while i <= FREQ_COUNT:
        detect_freq = freq[peak_args_sort[i]]

        if detect_freq <= (ALARM_FREQ + MARGIN) and detect_freq >= (ALARM_FREQ - MARGIN):
            PEAK_FLAG += 1

        i += 1

    return PEAK_FLAG


def kickAlart(beep, TIME):
    urllib.request.urlopen(ALEXA_URL)
    return


if __name__ == '__main__':
    P = pyaudio.PyAudio()
    stream = P.open(format=pyaudio.paInt16, channels=1, rate=RATE, frames_per_buffer=CHUNK, input=True, output=False)

    while stream.is_active():

        try:
            input = stream.read(CHUNK, exception_on_overflow=False)
            ndarray = np.frombuffer(input, dtype='int16')

            abs_array = np.abs(ndarray) / 32768

            #if abs_array.max() > 0.012:  # 拾う音レベル設定
            if abs_array.max() > 0.01:  # 拾う音レベル設定
                BEEP = getMaxFreqFFT(ndarray, CHUNK, freq)

                if BEEP > 0 and not in_beep:
                    in_beep = True
                    in_silence = False

                    checkTime = time.time()

                    beep_detected_count += 1

                    if beep_detected_count >= BEEP_REPEAT_COUNT:
                        nowTime = time.time()

                        # 操作音誤検知の為アラーム発動から5分以内は実行しない
                        if nowTime - alarm_time >= 300:
                            kickAlart(BEEP, nowTime)
                            timeRecord()
                            slack()

                        beep_detected_count = 0

                elif BEEP == 0 and not in_silence:
                    in_beep = False
                    in_silence = True

        except KeyboardInterrupt:
            break

    stream.stop_stream()
    stream.close()
    P.terminate()
