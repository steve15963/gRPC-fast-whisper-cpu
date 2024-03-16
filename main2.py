
import torchaudio
import subprocess
import json
import aiofiles
import asyncio
import time

from faster_whisper import WhisperModel
from datetime import datetime, timezone

async def ffprobe(path,name,type):
    # ffprobe 명령어 구성
    cmd = [
        'C:\\ffmpeg\\bin\\ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-select_streams', 'a',  # 오디오 스트림만 선택
        f"{path}/{name}.{type}"
    ]

    process = await asyncio.create_subprocess_shell(' '.join(cmd), stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, error = await process.communicate()

    # 출력 파싱
    info = json.loads(output)

    # 오디오 스트림 정보 추출
    if 'streams' in info and len(info['streams']) > 0:
        audio_info = info['streams']
        return audio_info
    else:
        print(error)
        return None
    
async def ffmpeg(path,name,type,audio_info):
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
    process = process = await asyncio.create_subprocess_shell(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = await process.communicate()
    return file_Info

async def mp4ToSrt(path,name,type):
    audio_info = await ffprobe(path,name,type)
    file_info = await ffmpeg(path,name,type,audio_info)

    model = WhisperModel(model_size_or_path='large', device="cuda", compute_type='float16')
    
    for metaData in file_info:
        #{"streamIndex":streamIndex,"channel":channel}
        # 파일 경로에서 직접 오디오 데이터 로드
        waveform, sample_rate = torchaudio.load(f'{path}/{name}_{metaData["streamIndex"]}.wav', format="wav")

        # 리샘플링
        transform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        pcmf32 = transform(waveform).squeeze().numpy()

        # # 트랜스크립션
        segments, info = model.transcribe(
            pcmf32, 
            language='ko', 
            word_timestamps=True,
            # vad_filter=True, # -> 데이터 오염 발생 원인
            # # 0 ~ 1, 실수, 0에 가까우면 정적, 1에 가까우면 창의적 
            temperature=0.0,
        )
        loop = asyncio.get_running_loop()

        print(info)

        #  텍스트 추출
        while True:
            segment = await loop.run_in_executor(None, next, segments, None)
            if segment is None:
                break
            words = segment.words
            if len(words) == 0 :
                continue
            text = ""
            for word in words :
                text = text + word.word
                # print(F"{name} : {word}")
            print(F"{name} : {words[0].start:03} - {words[-1].end:03} : {text}")
        print(f"{name} 끝")
            

async def main():
    jobList = []

    start = time.process_time_ns()
    jobList.append(
        asyncio.create_task(
            mp4ToSrt(
                ".",
                "test1",
                "mp4"
            )
        )
    )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test2",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test3",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test4",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test5",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test6",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test7",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test8",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test9",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test10",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test11",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test12",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test13",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test14",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test15",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test16",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test17",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test18",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test19",
    #             "mp4"
    #         )
    #     )
    # )
    # jobList.append(
    #     asyncio.create_task(
    #         mp4ToSrt(
    #             ".",
    #             "test20",
    #             "mp4"
    #         )
    #     )
    # )
    await asyncio.gather(*jobList)
    end = time.process_time_ns()

    print("동작 시간 : " , end - start)

asyncio.run(main())

# 모델 초기화