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
dt = 1 / RATE
freq = np.linspace(0, 1.0 / dt, CHUNK)
detect_freq = []
MARGIN = 10  # 周波数のマージン Hz
ALEXA_URL = 'http://10.0.1.6:1880/sentakuki/'  # Alexa通知サーバurl

BEEP_DURATION = 0.5
SILENCE_DURATION = 0.7
BEEP_REPEAT = 6

BEEP_DURATION = int(0.5 * RATE)  # Change to int(0.5 * RATE)
SILENCE_DURATION = int(0.7 * RATE)  # Change to int(0.7 * RATE)



def slack():
    slack = slackweb.Slack(url="https://hooks.slack.com/services/YOUR_KEY")
    slack.notify(text="洗濯機アラーム検知", channel="#private-fuka-ch", username="sentakuki-beep", icon_emoji=":raspberrypi:", mrkdwn=True)

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

    return detect_freq, PEAK_FLAG

def kickAlart():
    slack()
    urllib.request.urlopen(ALEXA_URL)
    return

if __name__ == '__main__':
    P = pyaudio.PyAudio()
    stream = P.open(format=pyaudio.paInt16, channels=1, rate=RATE, frames_per_buffer=CHUNK, input=True, output=False)

    beep_count = 0
    silence_count = 0
    total_count = 0
    beep_timer = 0
    silence_timer = 0



    while stream.is_active():
        total_count += 1

        if total_count >= LOOP_MAX:
            beep_count = 0
            silence_count = 0
            total_count = 0

        try:
            input = stream.read(CHUNK, exception_on_overflow=False)
            ndarray = np.frombuffer(input, dtype='int16')

            abs_array = np.abs
            abs_array = np.abs(ndarray) / 32768

            if abs_array.max() > 0.012:
                detect_freq, BEEP = getMaxFreqFFT(ndarray, CHUNK, freq)

                if BEEP:
                    beep_timer += CHUNK
                    silence_timer = 0
                    if beep_timer >= BEEP_DURATION:
                        beep_count += 1
                        beep_timer = 0
                else:
                    silence_timer += CHUNK
                    if silence_timer >= SILENCE_DURATION:
                        silence_count += 1
                        silence_timer = 0

                if beep_count >= BEEP_REPEAT and silence_count >= BEEP_REPEAT:
                    beep_count = 0
                    silence_count = 0

                    kickAlart()

            else:
                silence_count += 1

        except KeyboardInterrupt:
            break


    stream.stop_stream()
    stream.close()
    P.terminate()
