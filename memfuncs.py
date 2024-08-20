import pymem
import struct
from pymem import Pymem
from pymem.process import module_from_name
from ext_types import * 

class memfunc:
    
    def __init__(self, proc):
        self.proc = proc

    def GetProcess(self, procname):
        self.proc = Pymem(procname)
        return self.proc

    def GetModuleBase(self, modulename):
        if not modulename or not self.proc:
            return None
        
        module = module_from_name(self.proc.process_handle, modulename)
        if module:
            return module.lpBaseOfDll
        return None

    def ReadPointer(self, addy, offset=0):
        address = addy + offset
        return self.proc.read_longlong(address)

    def ReadBytes(self, addy, bytes_count):
        return self.proc.read_bytes(addy, bytes_count)

    def WriteBytes(self, address, newbytes):
        return self.proc.write_bytes(address, newbytes, len(newbytes))

    def ReadInt(self, address, offset=0):
        return self.proc.read_int(address + offset)

    def ReadLong(self, address, offset=0):
        return self.proc.read_longlong(address + offset)

    def ReadFloat(self, address, offset=0):
        return self.proc.read_float(address + offset)

    def ReadDouble(self, address, offset=0):
        return self.proc.read_double(address + offset)

    def ReadVec(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 12)
        x, y, z = struct.unpack('fff', bytes_)
        return Vector3(x, y, z)

    def ReadShort(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('h', bytes_)[0]

    def ReadUShort(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('H', bytes_)[0]

    def ReadUInt(self, address, offset=0):
        return self.proc.read_uint(address + offset)

    def ReadULong(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 8)
        return struct.unpack('Q', bytes_)[0]

    def ReadBool(self, address, offset=0):
        return self.proc.read_bool(address + offset)

    def ReadString(self, address, length, offset=0):
        return self.proc.read_string(address + offset, length)

    def ReadChar(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('c', bytes_)[0].decode('utf-8')

    def ReadMatrix(self, address):
        bytes_ = self.ReadBytes(address, 4 * 16)
        matrix = struct.unpack('16f', bytes_)
        return matrix

    def WriteInt(self, address, value, offset=0):
        return self.proc.write_int(address + offset, value)

    def WriteShort(self, address, value, offset=0):
        bytes_ = struct.pack('h', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteUShort(self, address, value, offset=0):
        bytes_ = struct.pack('H', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteUInt(self, address, value, offset=0):
        return self.proc.write_uint(address + offset, value)

    def WriteLong(self, address, value, offset=0):
        return self.proc.write_longlong(address + offset, value)

    def WriteULong(self, address, value, offset=0):
        bytes_ = struct.pack('Q', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteFloat(self, address, value, offset=0):
        return self.proc.write_float(address + offset, value)

    def WriteDouble(self, address, value, offset=0):
        return self.proc.write_double(address + offset, value)

    def WriteBool(self, address, value, offset=0):
        return self.proc.write_bool(address + offset, value)

    def WriteString(self, address, value, offset=0):
        return self.proc.write_string(address + offset, value)

    def WriteVec(self, address, value, offset=0):
        bytes_ = struct.pack('fff', value.x, value.y, value.z)
        return self.WriteBytes(address + offset, bytes_)


