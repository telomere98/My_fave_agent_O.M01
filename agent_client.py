from __future__ import division
import os
import re
import sys
import subprocess as sb
import time
import datetime
import json
import requests
import socket
import wave
from google.cloud import speech
import pyaudio
from six.moves import queue
from pydub import AudioSegment
from pydub.playback import play
sys.path.append(os.path.join(os.path.dirname(__file__), '/home/x19069/O.M01'))
from dialogue_system import DialogueSystem
from dialogue_system_bert import DialogueSystemBert
from emotion_estimator import EmotionEstimator

import io

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''#gcpで入手したjsonファイルのパス

HOST = "127.0.0.1"
MAINPORT = 50007
date = datetime.datetime.now()
logDate = date.strftime('%m%d-%H:%M:%S')
logId = date.strftime('%m%d%H')
audioArchive = 0
dialogue_system = DialogueSystem()
dialogue_system_bert = DialogueSystemBert()
emotion_estimator = EmotionEstimator()
tcp_client = None
mute = False
emoNum = 0
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
reply = "none"
talk = "none"
sendStr = "none"

class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            input_device_index=3, #本体マイク:1,マイクロフォンアレイ接続時:0
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        global mute
        #self._buff.put(in_data)
        if not mute:
            self._buff.put(in_data)
        #空データのやりとり
        else:
            in_data = bytes( [0 for i in range(len(in_data)) ] )
            self._buff.put(in_data)

        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

#音声認識
def listen_print_loop(responses):
    num_chars_printed = 0
    time_out = 0
    global mute
    for response in responses:
        time_out_st = time.perf_counter()
        if not response.results:
            continue
            print('1')

        result = response.results[0]
        if not result.alternatives:
            print('2')
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        #音声認識しきれなかった場合
        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            time_out_en = time.perf_counter()
            time_out_count = time_out_en - time_out_st
            time_out += time_out_count
            print('3: time out count: ' + str(time_out), flush = True)
            num_chars_printed = len(transcript)   
            #time out
            if time_out >= 0.01:
                print("time out")
                num_chars_printed = 0
                #認識結果とIDの格納
                input = {'utt': transcript + overwrite_chars, 'sessionId': str(logId)}
                #ネガポジスコアリング
                print("user_ee : " + emotion_estimator.sentiment_analysis_example(ee_client, input))
                talk = "user:" + transcript + overwrite_chars + "_ee;" + emotion_estimator.sentiment_analysis_example(ee_client, input)
                tcp_client.send(talk.encode('utf-8'))

                #対話システムでの応答作成
                if emoNum = 3 or emoNum = 4:
                    dialogue_input_nega(input)

                else:
                    dialogue_input(input)

                mute = True
                tcp_client.send(reply.encode('utf-8'))
                #データをunityから受け取る
                recv_data = tcp_client.recv(2)
                global emoNum = recv_data[1]
                print('recieved data:' + str(recv_data[0]) + 'emotionNum' + str(recv_data[1]))
                if recv_data[0] == 0:
                    mute = False
                time_out = 0

            else:
                time_out_st = time.perf_counter()

            #音声認識終了
        else:
            print(transcript + overwrite_chars)
            print('4')
                
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0
            #認識結果とIDの格納
            input = {'utt': transcript + overwrite_chars, 'sessionId': str(logId)}
            #ネガポジスコアリング
            print("user_ee : " + emotion_estimator.sentiment_analysis_example(ee_client, input))
            talk = "user:" + transcript + overwrite_chars + "_ee;" + emotion_estimator.sentiment_analysis_example(ee_client, input)
            tcp_client.send(talk.encode('utf-8'))

            #対話システムでの応答作成
            if emoNum = 3 or emoNum = 4:
                dialogue_input_nega(input)

            else:
                dialogue_input(input)

            mute = True
            tcp_client.send(reply.encode('utf-8'))
            #データをunityから受け取る
            recv_data = tcp_client.recv(2)
            global emoNum = recv_data[1]
            print('recieved data:' + str(recv_data[0]) + 'emotionNum' + str(recv_data[1]))
            if recv_data[0] == 0:
                mute = False
            time_out = 0
           

def dialogue_input(input):
     # log.txtに出力
    with open("/home/x19069/O.M01/log.txt", "a")as f:
        f.write(input["utt"] + ":" + input["sessionId"] + '\n') 

    #dialogue systemによる返答生成
    dialogue_output = dialogue_system_bert.aiml_reply(input)["utt"] #dialogue_output = dialogue_system.aiml_reply(input)["utt"]
    if dialogue_output == "shiftEbdm":
        dialogue_output = dialogue_system_bert.ebdm_reply(input)["utt"] #dialogue_output = dialogue_system.ebdm_reply(input)["utt"]
    print('reply : ' + dialogue_output)
    input = {'utt': dialogue_output}
    print("agent_ee : " + emotion_estimator.sentiment_analysis_example(ee_client, input))
    global reply
    reply = dialogue_output+ "_ee;" + emotion_estimator.sentiment_analysis_example(ee_client, input)

    #voicevoxで音声ファイルを作成
    generate_wav(dialogue_output)


def dialogue_input_nega(input):
     # log.txtに出力
    with open("/home/x19069/O.M01/log.txt", "a")as f:
        f.write(input["utt"] + ":" + input["sessionId"] + '\n') 

    #dialogue systemによる返答生成
    dialogue_output = dialogue_system_bert.aiml_reply(input)["utt"] #dialogue_output = dialogue_system.aiml_reply(input)["utt"]
    if dialogue_output == "shiftEbdm":
        dialogue_output = dialogue_system_bert.ebdm_reply_nega(input)["utt"] #dialogue_output = dialogue_system.ebdm_reply(input)["utt"]
    print('reply : ' + dialogue_output)
    input = {'utt': dialogue_output}
    print("agent_ee : " + emotion_estimator.sentiment_analysis_example(ee_client, input))
    global reply
    reply = dialogue_output+ "_ee;" + emotion_estimator.sentiment_analysis_example(ee_client, input)

    #voicevoxで音声ファイルを作成
    generate_wav(dialogue_output)    

# unityとのtcp通信用クライアント
def connect_unity():
   # TCP用のソケットを作成
   client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # テストのため自身のpidを表示
   result = str(os.getpid())
   print(os.getpid())
   # クライアントに接続
   client.connect((HOST, MAINPORT))
# 以降はclientを通してsendメソッドでデータを送れる
   return client

# voicevoxの処理
def generate_wav(text, speaker=14, filepath='/home/x19069/O.M01/voice.wav'):
    host = 'localhost'
    port = 50021
    global emoNum

    if emoNum == 2:
        params = (
            ('text', text),
            ('speaker', speaker),
            ('speedScale', 1.05),
            ('pitchScale', 1.02),
            ('intonationScale', 1.20),
        )

    else if emoNum == 3:
        params = (
            ('text', text),
            ('speaker', speaker),
            ('speedScale', 1.05),
            ('pitchScale', 0.97),
            ('intonationScale', 1.20),
        )

    else if emoNum == 3:
        params = (
            ('text', text),
            ('speaker', speaker),
            ('speedScale', 0.95),
            ('pitchScale', 0.97),
            ('intonationScale', 1.00),
        )    
    
    else:
         params = (
            ('text', text),
            ('speaker', speaker),
             ('speedScale', 1.00),
            ('pitchScale', 1.00),
            ('intonationScale', 1.00),
        )

    response1 = requests.post(
        f'http://{host}:{port}/audio_query',
        params=params
    )
    headers = {'Content-Type': 'application/json',}
    response2 = requests.post(
        f'http://{host}:{port}/synthesis',
        headers=headers,
        params=params,
        data=json.dumps(response1.json())
    )

    wf = wave.open(filepath, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(24000)
    wf.writeframes(response2.content)
    wf.close()


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "ja-JP"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )
    global mute
    global tcp_client
    global ee_client
    mute = False
    tcp_client = connect_unity()
    ee_client = emotion_estimator.authenticate_client()

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        #dialogue system initialize
        input = {'utt': None, 'sessionId': str(logId)}
        dialogue_system.aiml_init(input)
        
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)
    
   
        

if __name__ == "__main__":
    main()
