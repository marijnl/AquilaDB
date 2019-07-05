import grpc
from concurrent import futures
import time
import json

import proto.faiss_pb2_grpc as proto_server
import proto.faiss_pb2 as proto

from hfaiss.index import Faiss
faiss_ = Faiss()

class FaissServicer (proto_server.FaissServiceServicer):
    def initFaiss (self, request, context):
        response = proto.initFaissResponse()

        nlist = request.nlist # number of cells
        nprobe = request.nprobe # number of cells out of nlist
        bytesPerVec = request.bpv # number of bytes per vector
        bytesPerSubVec = request.bpsv # number of bytes per sub vector
        dim = request.vd # vector dimension
        matrix_ = request.matrix
        matrix = []
        # convert rpc matrix_ to python matrix
        for vector in matrix_:
            vector_e = vector.e
            vector_e_l = len(vector_e)
            # check if the vector length is below dimention limit
            # then pad vector with 0 by dimension
            if vector_e_l < dim:
                vector_e.extend([0]*(dim-vector_e_l))
            # make sure vector length doesn't exceed dimension limit
            matrix.append(vector_e[:dim])
            
        
        response.status = faiss_.initFaiss(nlist, nprobe, bytesPerVec, bytesPerSubVec, dim, matrix)
        return response

    def addVectors (self, request, context):
        response = proto.addVecResponse()
        
        documents = request.documents
        ret = faiss_.addVectors(documents)
        response.status = ret[0]
        response._id.extend(ret[1])
        return response

    def deleteVectors (self, request, context):
        response = proto.deleteVecResponse()

        ids = request._id

        ret = faiss_.deleteVectors(ids)
        response.status = ret[0]
        response._id.extend(ret[1])
        return response

    def getNearest (self, request, context):
        response = proto.getNearestResponse()

        matrix_ = request.matrix
        k = request.k
        matrix = []
        # convert rpc matrix_ to python matrix
        for vector in matrix_:
            vector_e = vector.e
            vector_e_l = len(vector_e)
            # check if the vector length is below dimention limit
            # then pad vector with 0 by dimension
            if vector_e_l < faiss_.dim:
                vector_e.extend([0]*(faiss_.dim-vector_e_l))
            # make sure vector length doesn't exceed dimension limit
            matrix.append(vector_e[:faiss_.dim])

        ret = faiss_.getNearest(matrix, k)
        response.status = ret[0]
        # ids_ = []
        # for id_ in ret[1]:
        #     ids_.append({"e": id_})
        # response.ids = json.dumps(ids_)
        # matrix_ = []
        # for vector in ret[2]:
        #     matrix_.append({"e": vector})
        # response.matrix = json.dumps(matrix_)
        response.ids = json.dumps(ret[1])
        response.dist_matrix = json.dumps(ret[2])
        return response

server = grpc.server(futures.ThreadPoolExecutor(max_workers = 1),  options=[
          ('grpc.max_send_message_length', 100 * 1024 * 1024),
          ('grpc.max_receive_message_length', 100 * 1024 * 1024) ])
proto_server.add_FaissServiceServicer_to_server (FaissServicer(), server)

print('Starting server. Listening on port 50052.')
server.add_insecure_port('[::]:50052')
server.start()

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)
