import base64
import hashlib
import os

from fastapi import HTTPException, status


def save_image_from_base64(base64_str, directory):
    try:
        image_data = base64.b64decode(base64_str)
    except base64.binascii.Error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 string"
        )
    hash_object = hashlib.sha256(image_data)
    filename = f"{hash_object.hexdigest()}.png"

    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, filename)
    with open(file_path, 'wb') as file:
        file.write(image_data)

    return file_path
