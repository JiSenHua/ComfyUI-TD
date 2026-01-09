from .node import *

NODE_CLASS_MAPPINGS = {
    "Comfy3DPacktoTD": Comfy3DPacktoTD,
    "Hy3DtoTD": Hy3DtoTD,
    "GaussianSplattingtoTD": GaussianSplattingtoTD,
    "ImagetoTD": ImagetoTD,
    "ImagetoTD(JPEG)": ImagetoTD_JPEG,
    "Tripo3DtoTD": Tripo3DtoTD,
    "TripoSRtoTD": TripoSRtoTD,
    "LoadTDImage": LoadTDImage,
    "VideotoTD": VideotoTD,
    "AudiotoTD": AudiotoTD,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Comfy3DPacktoTD": "Comfy3DPacktoTD",
    "Hy3DtoTD": "Hy3DtoTD",
    "GaussianSplattingtoTD": "3DGS to TouchDesigner",
    "ImagetoTD": "ImagetoTD",
    "ImagetoTD(JPEG)": "ImagetoTD(JPEG)",
    "Tripo3DtoTD": "Tripo3DtoTD",
    "TripoSRtoTD": "TripoSRtoTD",
    "LoadTDImage": "LoadTDImage",
    "VideotoTD": "VideotoTD",
    "AudiotoTD": "AudiotoTD",
}
