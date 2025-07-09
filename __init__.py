from .node import *

NODE_CLASS_MAPPINGS = {
    "Comfy3DPacktoTD": Comfy3DPacktoTD,
    "Hy3DtoTD": Hy3DtoTD,
    "ImagetoTD": ImagetoTD,
    "ImagetoTD(JPEG)": ImagetoTD_JPEG,
    "Tripo3DtoTD": Tripo3DtoTD,
    "TripoSRtoTD": TripoSRtoTD,
    "LoadTDImage": LoadTDImage,
    "VideotoTD": VideotoTD,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Comfy3DPacktoTD": "Comfy3DPacktoTD",
    "Hy3DtoTD": "Hy3DtoTD",
    "ImagetoTD": "ImagetoTD",
    "ImagetoTD(JPEG)": "ImagetoTD(JPEG)",
    "Tripo3DtoTD": "Tripo3DtoTD",
    "TripoSRtoTD": "TripoSRtoTD",
    "LoadTDImage": "LoadTDImage",
    "VideotoTD": "VideotoTD",
}
