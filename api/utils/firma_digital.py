# api/utils/firma_digital.py

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def firmar_con_llave_privada(data: str, key_path: str = 'keys/private-key.pem') -> str:
    try:
        with open(key_path, 'rb') as key_file:
            private_key = load_pem_private_key(key_file.read(), password=None)

        firma = private_key.sign(
            data.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        firma_b64 = base64.b64encode(firma).decode('utf-8')
        return firma_b64

    except Exception as e:
        raise Exception(f'Error al firmar: {str(e)}')
