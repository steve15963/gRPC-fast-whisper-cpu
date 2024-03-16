
import torchaudio
import subprocess
import json

from faster_whisper import WhisperModel
from datetime import datetime, timezone



def ffprobe(path,name,type):
    # ffprobe 명령어 구성
    cmd = [
        'C:\\ffmpeg\\bin\\ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-select_streams', 'a',  # 오디오 스트림만 선택
        f"{path}/{name}.{type}"
    ]

    process = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE)
    output, error = process.communicate()

    # 출력 파싱
    info = json.loads(output)

    # 오디오 스트림 정보 추출
    if 'streams' in info and len(info['streams']) > 0:
        audio_info = info['streams']
        return audio_info
    else:
        return None
    
def ffmpeg(path,name,type,audio_info):
    cmd = [
        'C:\\ffmpeg\\bin\\ffmpeg',
        '-y',
        '-i', f"{path}/{name}.{type}",
    ]
    file_Info = list()
    #n개의 스트림의 m개의 채널이 있음.
    for i, stream in enumerate(audio_info):
        streamIndex = stream['index']
        cmd.append(f'-map 0:a:{i}')
        cmd.append(f'-ac 1 -f wav -ar 8k -acodec pcm_s16le')
        cmd.append(f'{path}/{name}_{streamIndex}.wav')
        file_Info.append({"streamIndex":streamIndex})

    print(' '.join(cmd))
    process = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return file_Info

# 모델 초기화
model = WhisperModel(model_size_or_path='large', device="cuda", compute_type='float32')

path = "."
name = "binary"
type = "mp4"

audio_info = ffprobe(path,name,type)
file_info = ffmpeg(path,name,type,audio_info)


for metaData in file_info:
    #{"streamIndex":streamIndex,"channel":channel}
    # 파일 경로에서 직접 오디오 데이터 로드
    waveform, sample_rate = torchaudio.load(f'{path}/{name}_{metaData["streamIndex"]}.wav', format="wav")

    # 리샘플링
    transform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
    pcmf32 = transform(waveform).squeeze().numpy()

    # # 트랜스크립션
    segments, info = model.transcribe(pcmf32, language='ko', word_timestamps=True)

    # # 텍스트 추출
    lineNumber = 1
    with open(f'{path}/{name}_{metaData["streamIndex"]}.srt','w', encoding="utf-8") as file:
        for segment in segments :
            words = segment.words
            if len(words) == 0 :
                continue
            for word in words :
                start_time = datetime.fromtimestamp(word.start, tz=timezone.utc)
                end_time = datetime.fromtimestamp(word.end, tz=timezone.utc)
                print(start_time)
                file.write(f"{lineNumber}\n")
                file.write(f"{(start_time.hour):02}:{start_time.minute:02}:{start_time.second:02},{int(start_time.microsecond / 1000):03} --> {(end_time.hour):02}:{end_time.minute:02}:{end_time.second:02},{int(end_time.microsecond / 1000):03}\n")
                file.write(f"{word.word}\n\n")
                lineNumber = lineNumber + 1