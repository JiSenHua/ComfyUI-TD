from .node import *

NODE_CLASS_MAPPINGS = {
    "Comfy3DPacktoTD": Comfy3DPacktoTD,
    "Hy3DtoTD": Hy3DtoTD,
    "GaussianSplattingtoTD": GaussianSplattingtoTD,
    "ImagetoTD": ImagetoTD,
    "ImagetoTD(JPEG)": ImagetoTD_JPEG,
    "MasktoTD": MasktoTD,
    "Tripo3DtoTD": Tripo3DtoTD,
    "TripoSRtoTD": TripoSRtoTD,
    "LoadTDImage": LoadTDImage,
    "VideotoTD": VideotoTD,
    "AudiotoTD": AudiotoTD,
    "DataToTD": DataToTD,
    "TDtoSAM3Prompts": TDtoSAM3Prompts,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Comfy3DPacktoTD": "Comfy3DPacktoTD",
    "Hy3DtoTD": "Hy3DtoTD",
    "GaussianSplattingtoTD": "3DGStoTD",
    "ImagetoTD": "ImagetoTD",
    "ImagetoTD(JPEG)": "ImagetoTD(JPEG)",
    "MasktoTD": "MasktoTD",
    "Tripo3DtoTD": "Tripo3DtoTD",
    "TripoSRtoTD": "TripoSRtoTD",
    "LoadTDImage": "LoadTDImage",
    "VideotoTD": "VideotoTD",
    "AudiotoTD": "AudiotoTD",
    "DataToTD": "DataToTD",
    "TDtoSAM3Prompts": "TDtoSAM3Prompts",
}
