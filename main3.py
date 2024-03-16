import asyncio
import multiprocessing
import grpc
import io

from faster_whisper import WhisperModel

import orialz.sttgRPC_pb2 as sttgRPC_pb2
import orialz.sttgRPC_pb2_grpc as sttgRPC__pb2_grpc

class SpeechToTextServicer(sttgRPC__pb2_grpc.SpeechToTextServicer):
    model = WhisperModel(model_size_or_path='large', device="cpu", compute_type='int8')
    async def downloader(self,request):
        array = bytearray()
        async for data in request:
            array.extend(data.bin)
        return bytes(array)
    
    async def readyForSTT(self,bin):
        return self.model.transcribe(
            bin, 
            language='ko', 
            word_timestamps=True,
            # vad_filter=True,
            # # 0 ~ 1, 실수, 0에 가까우면 정적, 1에 가까우면 창의적 
            temperature=0.0,
        )

    async def toText(self, request, context):
        bin = io.BytesIO(await self.downloader(request))
        segments, info = await self.readyForSTT(bin)
        #segments는 지연 이터레이터 이므로 list로 변환하면 모두 처리하게 됨.
        segmentList = list(segments)
        textData = ''.join(word.word for segment in segmentList for word in segment.words)
        return sttgRPC_pb2.Text(text=textData)

    async def toStreamText(self, request, context):
        loop = asyncio.get_running_loop()
        bin = io.BytesIO(await self.downloader(request))
        segments, info = await self.readyForSTT(bin)
        while True:
            segment = await loop.run_in_executor(None, next, segments, None)
            if segment is None:
                break
        #for segment in segments:
            words = segment.words
            yield sttgRPC_pb2.StreamText(
                start=int(segment.start),
                end=int(segment.end),
                text=''.join(word.word for word in words)
        )

            

async def main():
    server = grpc.aio.server(
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 최대 전송 메시지 크기를 50MB로 설정
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)  # 최대 수신 메시지 크기를 50MB로 설정
        ]
    )
    listen_addr = '[::]:12345'
    sttgRPC__pb2_grpc.add_SpeechToTextServicer_to_server(
        SpeechToTextServicer(),
        server
    )
    server.add_insecure_port(listen_addr)
    await server.start()
    await server.wait_for_termination()


asyncio.run(main())

# 모델 초기화