import unittest
import logging
import sys
sys.path.append('../')
import asyncio
import grpc
from grpc import aio
import traceLog_pb2
import traceLog_pb2_grpc
from common import gRPCAddr
import time

# class MyTestCase(unittest.TestCase):
def test_grpc_client():
    async def run() -> None:
        for i in range(1):
            async with grpc.aio.insecure_channel(gRPCAddr) as channel:
                stub = traceLog_pb2_grpc.TraceLoggingStub(channel)
                if i % 2 == 0:
                    msg = traceLog_pb2.SignalMsg(turnOn=True, filePath='/Users/aaron/tmp/grpc_test.cell')
                else:
                    msg = traceLog_pb2.SignalMsg(turnOn=False, filePath='')
                response = await stub.SignalLogger(msg)
            print("Greeter client received: ", response)
            print(type(response), response)
            time.sleep(5)

    asyncio.run(run())


if __name__ == '__main__':
    test_grpc_client()
