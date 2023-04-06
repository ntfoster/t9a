import sys
import base64

def base_64_encode(filename):
    binary_fc = open(filename, 'rb').read()
    return base64.b64encode(binary_fc).decode('utf-8')

if __name__ == '__main__':
    print(base_64_encode(sys.argv[1]))
