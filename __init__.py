from .node import *

NODE_CLASS_MAPPINGS = {
    "Comfy3DPacktoTD": Comfy3DPacktoTD,
    "Hy3DtoTD": Hy3DtoTD,
    "GaussianSplattingtoTD": GaussianSplattingtoTD,
    "ImagetoTD": ImagetoTD,
    "ImagetoTD(JPEG)": ImagetoTD_JPEG,
    "ImagetoTD_Tagged": ImagetoTD_Tagged,
    "Tripo3DtoTD": Tripo3DtoTD,
    "TripoSRtoTD": TripoSRtoTD,
    "LoadTDImage": LoadTDImage,
    "VideotoTD": VideotoTD,
    "AudiotoTD": AudiotoTD,
    "StringtoTD": StringtoTD,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Comfy3DPacktoTD": "Comfy3DPacktoTD",
    "Hy3DtoTD": "Hy3DtoTD",
    "GaussianSplattingtoTD": "3DGStoTD",
    "ImagetoTD": "ImagetoTD",
    "ImagetoTD(JPEG)": "ImagetoTD(JPEG)",
    "ImagetoTD_Tagged": "ImagetoTD_Tagged",
    "Tripo3DtoTD": "Tripo3DtoTD",
    "TripoSRtoTD": "TripoSRtoTD",
    "LoadTDImage": "LoadTDImage",
    "VideotoTD": "VideotoTD",
    "AudiotoTD": "AudiotoTD",
    "StringtoTD": "StringtoTD",
}
