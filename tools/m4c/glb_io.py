"""Uncompressed glTF I/O for the exact validated Meshy asset; no mesh processing."""
import hashlib, json, struct
from pathlib import Path
import numpy as np
SOURCE_SHA = '421e593cad17f60d1c0c5e67707729fb88bbf69026795e22011ecc7d90b38959'
def sha(data): return hashlib.sha256(data).hexdigest()
def read_glb(path):
    raw=Path(path).read_bytes()
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
    chunks={}; pos=12
    while pos<len(raw):
        length,kind=struct.unpack_from('<II',raw,pos);pos+=8;chunks[kind]=raw[pos:pos+length];pos+=length
    return raw,json.loads(chunks[0x4e4f534a]),chunks[0x004e4942]
def accessor(doc,binary,index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    assert not view.get('byteStride') and not a.get('sparse')
    return np.frombuffer(binary,dtype=dtype,count=a['count']*width,offset=view.get('byteOffset',0)+a.get('byteOffset',0)).copy().reshape(-1,width)
def source(path):
    raw,doc,binary=read_glb(path);assert sha(raw)==SOURCE_SHA
    p=doc['meshes'][0]['primitives'][0]
    return doc,accessor(doc,binary,p['attributes']['POSITION']),accessor(doc,binary,p['attributes']['NORMAL']),accessor(doc,binary,p['indices']).reshape(-1,3)
def write_glb(path,doc,binary):
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    binary+=b'\0'*((-len(binary))%4)
    Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
