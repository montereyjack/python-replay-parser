import pprint
import sys
import struct

class ReplayParser:
    def __init__(self, debug=False):
        self.debug = debug

    def parse(self, replay_file):
        data = {}
        # TODO: CRC, version info, other stuff
        unknown = replay_file.read(20)
        header_start = replay_file.read(24)

        data['header'] = self._read_properties(replay_file)
        unknown = self._read_unknown(replay_file, 8)
        data['level_info'] = self._read_level_info(replay_file)
        data['key_frames'] = self._read_key_frames(replay_file)
        return data

    def _sniff_bytes(self, replay_file, size):
        b = self._read_unknown(replay_file, size)
        print("**** BYTES ****")
        print("Bytes: {}".format(self._pretty_byte_string(b)))
        if size == 2:
            print("Short: Signed: {} Unsigned: {}".format(struct.unpack('<h', b), struct.unpack('<H', b)))
        else:
            print("Integer: Signed: {}, Unsigned: {}".format(struct.unpack('<i', b), struct.unpack('<I', b)))
            print("Float: {}".format(struct.unpack('<f', b)))

    def _read_properties(self, replay_file):
        results = {}

        while True:
            property_info = self._read_property(replay_file)
            if property_info:
                results[property_info['name']] = property_info['value']
            else:
                return results

    def _read_property(self, replay_file):
        if self.debug: print("Reading name")
        name_length = self._read_integer(replay_file, 4)
        property_name = self._read_string(replay_file, name_length)
        if self.debug: print("Property name: {}".format(property_name))

        if property_name == 'None':
            return None

        if self.debug: print("Reading type")
        type_length = self._read_integer(replay_file, 4)
        type_name = self._read_string(replay_file, type_length)
        if self.debug: print("Type name: {}".format(type_name))

        if self.debug: print("Reading value")
        if type_name == 'IntProperty':
            value_length = self._read_integer(replay_file, 8)
            value = self._read_integer(replay_file, value_length)
        elif type_name == 'StrProperty':
            unknown = self._read_integer(replay_file, 8)
            length = self._read_integer(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'FloatProperty':
            length = self._read_integer(replay_file, 8)
            value = self._read_float(replay_file, length)
        elif type_name == 'NameProperty':
            unknown = self._read_integer(replay_file, 8)
            length = self._read_integer(replay_file, 4)
            value = self._read_string(replay_file, length)
        elif type_name == 'ArrayProperty':
            # I imagine that this is the length of bytes that the data
            # in the "array" actually take up in the file.
            unknown = self._read_integer(replay_file, 8)
            array_length = self._read_integer(replay_file, 4)

            value = [
                self._read_properties(replay_file)
                for x in range(array_length)
            ]

        if self.debug: print("Value: {}".format(value))

        return { 'name' : property_name, 'value': value}

    def _read_level_info(self, replay_file):
        map_names = []
        number_of_maps = self._read_integer(replay_file, 4)
        for x in range(number_of_maps):
            map_name_length = self._read_integer(replay_file, 4)
            map_name = self._read_string(replay_file, map_name_length)
            map_names.append(map_name)

        return map_names

    # I'm not sure if they're actually called "key frames", but it seems to be a 
    # list of frames, along with some other number...
    def _read_key_frames(self, replay_file):
        number_of_key_frames = self._read_integer(replay_file, 4)
        key_frames = [
            self._read_key_frame(replay_file)
            for x in range(number_of_key_frames)
        ]
        zero_byte = self._read_unknown(replay_file, 1)
        return key_frames

    def _read_key_frame(self, replay_file):
        time = self._read_float(replay_file, 4)
        frame = self._read_integer(replay_file, 4)
        unknown_number = self._read_integer(replay_file, 4)
        return {
            'time' : time,
            'frame' : frame,
            '???' : unknown_number
        }

    def _pretty_byte_string(self, bytes_read):
        return ':'.join(format(ord(x), '#04x') for x in bytes_read)

    def _print_bytes(self, bytes_read):
        print('Hex read: {}'.format(self._pretty_byte_string(bytes_read)))

    def _read_integer(self, replay_file, length, signed=True):
        if signed:
            number_format = {
                1: '<b',
                2: '<h',
                4: '<i',
                8: '<q',
            }[length]
        else:
            number_format = {
                1: '<B',
                2: '<H',
                4: '<I',
                8: '<Q'
            }[length]

        bytes_read = replay_file.read(length)
        if self.debug: self._print_bytes(bytes_read)
        value = struct.unpack(number_format, bytes_read)[0]
        if self.debug: print("Integer read: {}".format(value))
        return value

    def _read_float(self, replay_file, length):
        number_format = {
            4: '<f',
            8: '<d'
        }[length]
        bytes_read = replay_file.read(length)
        if self.debug: self._print_bytes(bytes_read)
        value = struct.unpack(number_format, bytes_read)[0]
        if self.debug: print ("Float read: {}".format(value))
        return value

    def _read_unknown(self, replay_file, num_bytes):
        bytes_read = replay_file.read(num_bytes)
        if self.debug: self._print_bytes(bytes_read)
        return bytes_read

    def _read_string(self, replay_file, length):
        bytes_read = replay_file.read(length)[0:-1]
        if self.debug: self._print_bytes(bytes_read)
        return bytes_read


if __name__ == '__main__':
    filename = sys.argv[1]
    if not filename.endswith('.replay'):
        sys.exit('Filename {} does not appear to be a valid replay file'.format(filename))

    with open(filename, 'rb') as replay_file:
        results = ReplayParser(debug=False).parse(replay_file)
        try:
            pprint.pprint(results)
        except IOError as e:
            pass
