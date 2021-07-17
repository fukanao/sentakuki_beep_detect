# 洗濯機のアラーム音を検知してAmazon Echoで知らせる

import os
import pyaudio
import numpy as np
import time
import urllib.request
import slackweb
from scipy.signal import argrelmax

# setting
CHUNK = 1024
RATE = 8000 # サンプリング周波数
ALARM_FREQ = 2000 # アラーム音の周波数
FREQ_COUNT = 3 # 最大音量の周波数カウント数
PEAK_COUNT = 0
LOOP_MAX = 100 # 誤検知回避のためカウント回数リセット
dt = 1/RATE
freq = np.linspace(0,1.0/dt,CHUNK)
detect_freq = []
MARGIN = 3 # 周波数のマージン Hz
ALEXA_URL = 'http://10.0.1.5:1880/sentakuki/' # Alexa通知サーバurl

# 連続Alexa通知防止用時間記録ファイル作成
def timeRecord():
    f = open('previous.dat','w')
    TIME = time.time()
    f.write(str(TIME))
    f.close

# Slack通知
def slack():
     slack = slackweb.Slack(url="https://hooks.slack.com/services/xxxxxxxxx")
     slack.notify(text="洗濯機アラーム検知", channel="#xxxxxxxx", username="sentakuki-beep", icon_emoji=":raspberrypi:", mrkdwn=True)


# FFT
def getMaxFreqFFT(sound, chunk, freq):
    f = np.fft.fft(sound)/(chunk/2)
    f_abs = np.abs(f)

    #ピーク検出
    peak_args = argrelmax(f_abs[:(int)(chunk/2)], order=8) #前半のピークのリスト番号
    f_peak = f_abs[peak_args]
    f_peak_argsort = f_peak.argsort()[::-1] #ピークの周波数数列をソート
    peak_args_sort = peak_args[0][f_peak_argsort]

    i = 0 
    PEAK_FLAG = 0

    while  i <= FREQ_COUNT:
        detect_freq = freq[peak_args_sort[i]] 

        if detect_freq <= (ALARM_FREQ + MARGIN) and detect_freq >= (ALARM_FREQ - MARGIN):
            PEAK_FLAG += 1

        i += 1

    return PEAK_FLAG


# Beep検出時アラート発行
def kickAlart(beep, TIME):
    slack()
    urllib.request.urlopen(ALEXA_URL)
    return


# メイン

if __name__=='__main__':
    P = pyaudio.PyAudio()
    stream = P.open(format=pyaudio.paInt16, channels=1, rate=RATE, frames_per_buffer=CHUNK, input=True, output=False)

    LOOP = 0 #ループカウント
    
    while stream.is_active():

        LOOP += 1

        if LOOP >= LOOP_MAX:
            PEAK_COUNT = 0
            LOOP = 0
        try:
            input = stream.read(CHUNK, exception_on_overflow=False)
            ndarray = np.frombuffer(input, dtype='int16')

            abs_array = np.abs(ndarray)/32768

            if abs_array.max() > 0.01: #拾う音レベル設定

                BEEP = getMaxFreqFFT(ndarray, CHUNK, freq)
                PEAK_COUNT = PEAK_COUNT + BEEP

                if PEAK_COUNT >= 8: # ピークカウント数

                    nowTime = time.time()
                    previousTime = os.path.getmtime('previous.dat')
                    PEAK_COUNT = 0

                    # 前の実行時間と比較,100秒以内だとAlexaに通知しない
                    # 洗濯機操作時連続Alexa通知防止
                    if nowTime - previousTime >= 100:
                        kickAlart(BEEP, nowTime)
                        timeRecord() # アラート実行時間記録

        except KeyboardInterrupt:
            break

    stream.stop_stream()
    stream.close()
    P.terminate()
