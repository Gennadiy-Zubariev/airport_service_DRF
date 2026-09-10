import pathlib
import uuid
from django.utils.text import slugify


def airplane_image_path(instance, filename):
    filename = f"{ slugify(instance.name)}-{uuid.uuid4()}" + pathlib.Path(filename).suffix
    return pathlib.Path("upload/buses") / pathlib.Path(filename)