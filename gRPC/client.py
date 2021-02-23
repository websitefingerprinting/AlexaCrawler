import grpc
import traceLog_pb2
import traceLog_pb2_grpc
import time
import google.protobuf.empty_pb2


class GRPCClient:
    def __init__(self, gRPCAddr):
        self.gRPCAddr = gRPCAddr

    def sendRequest(self, turn_on = False, file_path = '') -> Exception:
        try:
            with grpc.insecure_channel(self.gRPCAddr) as channel:
                stub = traceLog_pb2_grpc.TraceLoggingStub(channel)
                signal = traceLog_pb2.SignalMsg(turnOn = turn_on, filePath = file_path)
                _ = stub.SignalLogger(signal)
                return None
        except Exception as e:
            return e

# if __name__ == '__main__':
#     client = GRPCClient("localhost:10086")
#     ok = client.sendRequest(True, '/Users/aaron/tmp/test.cell')
#
#     print(ok)
