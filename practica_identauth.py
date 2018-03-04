from math import ceil
from Crypto.Cipher import DES
from Crypto.Cipher import DES3
from sys import argv


iv = "0000000000000000"
mk = None
sk = None

def ByteToHex( byteStr ):
    # https://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/
    return ''.join( [ "%02X" % ord( x ) for x in byteStr ] ).strip()

def HexToByte( hexStr ):
    # https://code.activestate.com/recipes/510399-byte-to-hex-and-hex-to-byte-string-conversion/
    byte = []
    hexStr = ''.join( hexStr.split(" ") )
    for i in range(0, len(hexStr), 2):
        byte.append( chr( int (hexStr[i:i+2], 16 ) ) )
    return ''.join( byte )

def calcula_des(clave8B, data):
    key = HexToByte(clave8B)
    cipher = DES.new(key, DES.MODE_CBC, HexToByte(iv))
    return cipher.encrypt(data) # devuelve byte string

def calcula_3des(clave16B, data):
    # data ya esta en byte string, ya que es el resultador del calcula_xor
    key = HexToByte(clave16B)
    cipher = DES3.new(key, DES3.MODE_CBC, HexToByte(iv))
    return cipher.encrypt(data) # devuelve byte string

def calcula_xor(data1, data2):
    # print data1, ByteToHex(data2)
    # print ByteToHex(''.join([chr(ord(b1) ^ ord(b2)) for (b1, b2) in zip(HexToByte(data1), data2)])) # devuelve byte string
    return ''.join([chr(ord(b1) ^ ord(b2)) for (b1, b2) in zip(HexToByte(data1), data2)]) # devuelve byte string

def calcula_ultimos_3bytes(bloques, sk):
    # ultimo_bloque esta en byte string, \xff\x0a..
    # bloq esta en hexadecimal string, FF0A..
    ultimo_bloque = HexToByte(iv) # 00..00
    sk1 = sk[:16] # sk es formato FFAA...00
    for i, bloq in enumerate(bloques):
        # print("Bloq_actual: " + bloq + " Ult_bloq: " + ByteToHex(ultimo_bloque))
        # print("Xor: " + ByteToHex(calcula_xor(bloq, ultimo_bloque)))
        if i == len(bloques)-1:
            ultimo_bloque = calcula_3des(sk, calcula_xor(bloq, ultimo_bloque))
            # print("3Des: " + ByteToHex(ultimo_bloque))
        else:
            ultimo_bloque = calcula_des(sk1, calcula_xor(bloq, ultimo_bloque))
            # print("Des: " + ByteToHex(ultimo_bloque))
    return ultimo_bloque

def calcula_bloques_cifrados(bloques, sk):
    # ultimo_bloque esta en byte string, \xff\x0a..
    # bloq esta en hexadecimal string, FF0A..
    ultimo_bloque = HexToByte(iv) # 00..00
    bloq_cifrados = []
    for i, bloq in enumerate(bloques):
        # print("Bloq_actual: " + bloq + " Ult_bloq: " + ByteToHex(ultimo_bloque))
        # print("Xor: " + ByteToHex(calcula_xor(bloq, ultimo_bloque)))
        ultimo_bloque = calcula_3des(sk, calcula_xor(bloq, ultimo_bloque))
        # print("CB" + str(i) + ": " + ByteToHex(ultimo_bloque))
        bloq_cifrados.append(ByteToHex(ultimo_bloque))
    # print("Cifrado: " + "".join(bloq_cifrados))
    return "".join(bloq_cifrados)

def verifica_padding(data):
    tam = len(HexToByte(data))
    if tam != 8:
        padding = (8 - tam) * "00"
        data = data + padding
    return data

def split_hex(data, size):
	return [data[i:i+size] for i in range(0, len(data), size)]

def calcula_clave_sesion(mk, gr):
    global sk
    mk2mk1 = mk[16:]+mk[:16]
    nt = gr[:4] # 00NT XX..CRN
    nt_data = "000000" + nt + "000000"
    # print("nt_data: " + nt_data)
    sk1 = calcula_3des(mk, HexToByte(nt_data))
    # print("sk1: " + ByteToHex(sk1))
    sk2 = calcula_3des(mk2mk1, HexToByte(nt_data))
    # print("sk2: " + ByteToHex(sk2))
    sk = ByteToHex(sk1 + sk2)
    # print("sk: " + sk)
    return sk


def leer_datos_uso_1():
    # Calcular clave de sesion, usa MK y getResponse
    global mk
    if mk is None:
        mk = raw_input("Introduzca MK: ")
        assert len(HexToByte(mk)) == 16, "MK no tiene tamano 16B"
        print("MK = " + " ".join(split_hex(mk, 2)))
    else:
        yes = raw_input("MK en memoria: " + " ".join(split_hex(mk, 2)) + "\n" +
                        "Usar este MK? [Y/n]: ")
        if yes == 'n':
            mk = raw_input("Introduzca MK: ")
            assert len(HexToByte(mk)) == 16, "MK no tiene tamano 16B"
            print("MK = " + " ".join(split_hex(mk, 2)))
        else:
            print("Usando MK de memoria")

    gr = raw_input("Introduzca respuesta tras internal authenticate (getResponse): ")
    assert len(HexToByte(gr)) == 10, "GetResponse no tiene tamano 10B"
    print("GetResponse = " + " ".join(split_hex(gr, 2)))

    return mk, gr

def leer_datos_uso_2():
    # Calcula 3B menos significativos del ultimo bloque tras hacer DES + XOR .... XOR + 3DES
    # Usa clave de sesion (la pide en caso de que no exista en memoria), instrucciones (con L+3) y datos
    global sk
    if sk is None:
        sk = raw_input("Introduzca SK: ")
        assert len(HexToByte(sk)) == 16, "SK no tiene tamano 16B"
        print("SK = " + " ".join(split_hex(sk, 2)))
    else:
        yes = raw_input("SK en memoria: " + " ".join(split_hex(sk, 2)) + "\n" +
                        "Usar este SK? [Y/n]: ")
        if yes == 'n':
            sk = raw_input("Introduzca SK: ")
            assert len(HexToByte(sk)) == 16, "SK no tiene tamano 16B"
            print("SK = " + " ".join(split_hex(sk, 2)))
        else:
            print("Usando SK de memoria")


    ins = raw_input("Introduzca las instrucciones, con L+3: ")
    assert len(HexToByte(ins)) == 5, "Instrucciones no tiene tamano 5B"
    print("INS = " + " ".join(split_hex(ins, 2)))

    data = raw_input("Introduzca los datos: ")
    print("DATOS = " + " ".join(split_hex(data, 2)))

    return sk, ins, data

def leer_datos_uso_3():
    global sk
    if sk is None:
        sk = raw_input("Introduzca SK: ")
        assert len(HexToByte(sk)) == 16, "SK no tiene tamano 16B"
        print("SK = " + " ".join(split_hex(sk, 2)))
    else:
        yes = raw_input("SK en memoria: " + " ".join(split_hex(sk, 2)) + "\n" +
                        "Usar este SK? [Y/n]: ")
        if yes.lower() == 'n':
            sk = raw_input("Introduzca SK: ")
            assert len(HexToByte(sk)) == 16, "SK no tiene tamano 16B"
            print("SK = " + " ".join(split_hex(sk, 2)))
        else:
            print("Usando SK de memoria")

    datos = raw_input("Introduzca datos a cifrar: ")
    assert len(HexToByte(datos)) % 2 == 0, "Hexadecimal erroneo"
    print("DATOS = " + " ".join(split_hex(datos, 2)))

    return sk, datos

def main():
    print(""""Indique con un numero la actividad a realizar:

    *1: Generar clave de sesion, recibe getResponse del internal authenticate y clave administrativa.
    *2: Calcular ultimo bloque, recibe clave de sesion si no se ha calculado previamente en el paso 1,
        las instrucciones (L+3) y los datos a enviar.
    *3: Cifrar datos, recibe clave de sesion si no se ha calculado previamente en el paso 1
        y los datos a cifrar.
    *4: Terminar programa.""")

    global sk

    while True:
        inp = raw_input("\nSeleccion: ")
        inp = int(inp)

        if inp == 1:
            if sk is not None:
                yes = raw_input("SK en memoria: " + " ".join(split_hex(sk, 2)) + "\n" +
                                "Usar este SK? [Y/n]: ")
                if yes.lower() == 'n':
                    mk, gr = leer_datos_uso_1()
                    sk = calcula_clave_sesion(mk, gr)
                    print("SK: " + sk)
                else:
                    print("Usando SK de memoria")
            else:
                mk, gr = leer_datos_uso_1()
                sk = calcula_clave_sesion(mk, gr)
                print("SK: " + sk)

        elif inp == 2:
            sk, ins, data = leer_datos_uso_2()
            n_bloques = ceil((len(ins)/2.0 + len(data)/2.0)/8.0)
            assert n_bloques > 0, "Debe existir al menos un bloque"
            bloques = []
            xor = 8 * "00"
            if n_bloques == 1:
                data = verifica_padding(data)
                bloques.append(data)
                bloques.append(8 * "00")
            else:
                to_split = ins + data
                bloq_size = 16 # 2 elements per byte, 8 bytes
                bloques = split_hex(to_split, bloq_size)
                bloques = [verifica_padding(bloq) for bloq in bloques]

            print("Ultimo Bloque: " + ByteToHex(calcula_ultimos_3bytes(bloques, sk)))

        elif inp == 3:
            sk, datos = leer_datos_uso_3()
            bloq_size = 16 # 2 elements per byte, 8 bytes
            bloques = split_hex(datos, bloq_size)
            bloques = [verifica_padding(bloq) for bloq in bloques]
            print("CDATOS: " + calcula_bloques_cifrados(bloques, sk))

        elif inp == 4:
            print("Saliendo")
            break
        else:
            print("Error, seleccione una actividad del 1 al 4")

    # sk1 = "F1CCDA3251E5A0D0"
    # sk = "F1CCDA3251E5A0D03D3863D71EFA838F"
    # ins = "04D6000013"
    # data = "01010101010101010101010101010101"

if __name__ == "__main__":
	main()
