import pathlib
import uuid
from django.utils.text import slugify


def airplane_image_path(instance, filename):
    filename = (
        f"{slugify(instance.name)}-{uuid.uuid4()}"
        + pathlib.Path(filename).suffix
    )
    return pathlib.Path("upload/buses") / pathlib.Path(filename)


def params_to_ints(query_string):
    return [int(param) for param in query_string.split(",")]


def validate_seat(seat: int, num_seats: int, error_to_raise):
    if not (1 <= seat <= num_seats):
        raise error_to_raise(
            {"seat": f"seat must be in range [1, {num_seats}] not {seat}"}
        )


def validate_row(row: int, num_rows: int, error_to_raise):
    if not (1 <= row <= num_rows):
        raise error_to_raise(
            {"row": f"row must be in range [1, {num_rows}] not {row}"}
        )
