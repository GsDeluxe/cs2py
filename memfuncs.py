import pymem
import struct
from pymem import Pymem
from pymem.process import module_from_name
from ext_types import *

# Memory manipulation class for reading/writing process memory
class MemoryFunctions:
    
    def __init__(self, proc=None):
        self.proc = proc

    def get_process(self, procname):
        """Attach to a process by name"""
        self.proc = Pymem(procname)
        return self.proc

    def get_module_base(self, modulename):
        """Get base address of a module in the process"""
        if not modulename or not self.proc:
            return None
        
        module = module_from_name(self.proc.process_handle, modulename)
        if module:
            return module.lpBaseOfDll
        return None

    # Memory read operations
    def read_pointer(self, address, offset=0):
        """Read 64-bit pointer"""
        return self.proc.read_longlong(address + offset)

    def read_bytes(self, address, size):
        """Read raw bytes"""
        return self.proc.read_bytes(address, size)

    def read_int(self, address, offset=0):
        """Read 32-bit integer"""
        return self.proc.read_int(address + offset)

    def read_uint(self, address, offset=0):
        """Read unsigned 32-bit integer"""
        return self.proc.read_uint(address + offset)

    def read_long(self, address, offset=0):
        """Read 64-bit integer"""
        return self.proc.read_longlong(address + offset)

    def read_ulong(self, address, offset=0):
        """Read unsigned 64-bit integer"""
        bytes_ = self.read_bytes(address + offset, 8)
        return struct.unpack('Q', bytes_)[0]

    def read_short(self, address, offset=0):
        """Read 16-bit integer"""
        bytes_ = self.read_bytes(address + offset, 2)
        return struct.unpack('h', bytes_)[0]

    def read_ushort(self, address, offset=0):
        """Read unsigned 16-bit integer"""
        bytes_ = self.read_bytes(address + offset, 2)
        return struct.unpack('H', bytes_)[0]

    def read_float(self, address, offset=0):
        """Read 32-bit float"""
        return self.proc.read_float(address + offset)

    def read_double(self, address, offset=0):
        """Read 64-bit float"""
        return self.proc.read_double(address + offset)

    def read_bool(self, address, offset=0):
        """Read boolean value"""
        return self.proc.read_bool(address + offset)

    def read_string(self, address, length, offset=0):
        """Read string of specified length"""
        return self.proc.read_string(address + offset, length)

    def read_char(self, address, offset=0):
        """Read single character"""
        bytes_ = self.read_bytes(address + offset, 2)
        return struct.unpack('c', bytes_)[0].decode('utf-8')

    def read_vector3(self, address, offset=0):
        """Read 3D vector (x,y,z floats)"""
        bytes_ = self.read_bytes(address + offset, 12)
        x, y, z = struct.unpack('fff', bytes_)
        return Vector3(x, y, z)

    def read_matrix(self, address):
        """Read 4x4 float matrix"""
        bytes_ = self.read_bytes(address, 4 * 16)
        return struct.unpack('16f', bytes_)

    # Memory write operations
    def write_bytes(self, address, data):
        """Write raw bytes"""
        return self.proc.write_bytes(address, data, len(data))

    def write_int(self, address, value, offset=0):
        """Write 32-bit integer"""
        return self.proc.write_int(address + offset, value)

    def write_uint(self, address, value, offset=0):
        """Write unsigned 32-bit integer"""
        return self.proc.write_uint(address + offset, value)

    def write_long(self, address, value, offset=0):
        """Write 64-bit integer"""
        return self.proc.write_longlong(address + offset, value)

    def write_ulong(self, address, value, offset=0):
        """Write unsigned 64-bit integer"""
        bytes_ = struct.pack('Q', value)
        return self.write_bytes(address + offset, bytes_)

    def write_short(self, address, value, offset=0):
        """Write 16-bit integer"""
        bytes_ = struct.pack('h', value)
        return self.write_bytes(address + offset, bytes_)

    def write_ushort(self, address, value, offset=0):
        """Write unsigned 16-bit integer"""
        bytes_ = struct.pack('H', value)
        return self.write_bytes(address + offset, bytes_)

    def write_float(self, address, value, offset=0):
        """Write 32-bit float"""
        return self.proc.write_float(address + offset, value)

    def write_double(self, address, value, offset=0):
        """Write 64-bit float"""
        return self.proc.write_double(address + offset, value)

    def write_bool(self, address, value, offset=0):
        """Write boolean value"""
        return self.proc.write_bool(address + offset, value)

    def write_string(self, address, value, offset=0):
        """Write string"""
        return self.proc.write_string(address + offset, value)

    def write_vector3(self, address, value, offset=0):
        """Write 3D vector (x,y,z floats)"""
        bytes_ = struct.pack('fff', value.x, value.y, value.z)
        return self.write_bytes(address + offset, bytes_)
