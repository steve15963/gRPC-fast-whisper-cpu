import orialz.sttgRPC_pb2 as sttgRPC_pb2
import orialz.sttgRPC_pb2_grpc as sttgRPC__pb2_grpc

import asyncio
import grpc
import aiofiles

async def fileUploader(file):
    async with aiofiles.open(file, 'rb') as file:
        while True:
            # default : 4MB이므로 대용량의 파일의 경우 컨텍스트 스위칭 비용이 너무 많음.
            # 삭제를 진행하도록.
            # 50 * 1024 * 1024 * 0.95 = 49807360
            data = await file.read(49807360)
            if not data:
                return
            yield sttgRPC_pb2.Sound(bin = data)

async def task(i,channel,file,semaphore):
    stub = sttgRPC__pb2_grpc.SpeechToTextStub(channel)
    async with semaphore :
        responses = stub.toStreamText(fileUploader(file))
        async for response in responses:
            print(f"{i:03} : {response.start:010} - {response.end:010} : {response.text}")

async def task2(i,channel,file,semaphore):
    stub = sttgRPC__pb2_grpc.SpeechToTextStub(channel)
    async with semaphore :
        response = await stub.toText(fileUploader(file))
        print(f"{i}")

async def main():
    fileList = [
        "test1_1.wav",
        "test2_1.wav",
    ]
    semaphore = asyncio.Semaphore(1000)
    channel = grpc.aio.insecure_channel(
        "localhost:12345",
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 최대 전송 메시지 크기를 50MB로 설정
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)  # 최대 수신 메시지 크기를 50MB로 설정
        ]
    )
    
    launcherObject = list()
    for i,file in enumerate(fileList) :
        launcherObject.append(
            asyncio.create_task(
                task(i,channel,file,semaphore)
            )
        )
    await asyncio.gather(*launcherObject)

asyncio.run(main())