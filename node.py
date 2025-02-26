import trimesh
import struct
import numpy as np
import io
from server import PromptServer, BinaryEventTypes
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import torch

class Hy3DtoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trimesh": ("TRIMESH",),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_mesh"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_mesh(self, trimesh, broadcast):
        processed_mesh = self.process_mesh(trimesh)
        return self._send_to_td(processed_mesh, broadcast)

    def process_mesh(self, mesh):
        try:
            if isinstance(mesh, trimesh.Scene):
                meshes = []
                for m in mesh.geometry.values():
                    if isinstance(m, trimesh.Trimesh):
                        meshes.append(m)
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    raise ValueError("No valid mesh data found")

            if not isinstance(mesh, trimesh.Trimesh):
                raise ValueError("Input data is not a valid Trimesh object")

            mesh.fix_normals()

            if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
                pass
            elif hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
                mesh.visual = mesh.visual.to_color()
            else:
                mesh.visual = trimesh.visual.ColorVisuals(mesh)
                mesh.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(mesh.vertices), 1))

            return mesh

        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def _send_to_td(self, mesh, broadcast):
        try:
            buffer = io.BytesIO()
            mesh.export(file_obj=buffer, file_type='ply')
            binary_data = buffer.getvalue()
            buffer.close()

            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(1000, binary_data, sid=sid)

            return {"ui": {
                "mesh": [{
                    "source": "websocket",
                    "content-type": "model/ply",
                    "type": "output",
                }]
            }}
        except Exception as e:
            raise ValueError(f"Error sending mesh: {str(e)}")


class Tripo3DtoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_file": ("STRING",),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_mesh"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_mesh(self, model_file, broadcast):
        processed_mesh = self.process_mesh(model_file)
        return self._send_to_td(processed_mesh, broadcast)

    def process_mesh(self, model_file):
        try:
            mesh = trimesh.load(model_file)

            if isinstance(mesh, trimesh.Scene):
                meshes = []
                for m in mesh.geometry.values():
                    if isinstance(m, trimesh.Trimesh):
                        self._process_vertex_colors(m)
                        meshes.append(m)

                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    raise ValueError("No valid mesh data found")

            if not isinstance(mesh, trimesh.Trimesh):
                raise ValueError("Input data is not a valid Trimesh object")

            mesh.fix_normals()

            if not hasattr(mesh.visual, 'vertex_colors') or mesh.visual.vertex_colors is None:
                mesh.visual = trimesh.visual.ColorVisuals(mesh)
                mesh.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(mesh.vertices), 1))
            else:
                if mesh.visual.vertex_colors.max() <= 1.0:
                    mesh.visual.vertex_colors = (mesh.visual.vertex_colors * 255).astype(np.uint8)
                else:
                    mesh.visual.vertex_colors = mesh.visual.vertex_colors.astype(np.uint8)

            return mesh

        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def _process_vertex_colors(self, m):
        try:
            if not hasattr(m.visual, 'vertex_colors') or m.visual.vertex_colors is None:
                if hasattr(m.visual, 'material'):
                    material = m.visual.material
                    if hasattr(material, 'baseColorTexture') and material.baseColorTexture is not None:
                        if hasattr(m.visual, 'uv') and m.visual.uv is not None:
                            self._extract_colors_from_texture(m)
                    elif hasattr(material, 'baseColorFactor'):
                        color = np.array(material.baseColorFactor)
                        if len(color) == 3:
                            color = np.append(color, 1.0)
                        color = np.clip(color, 0, 1)
                        color = (color * 255).astype(np.uint8)
                        m.visual = trimesh.visual.ColorVisuals(m)
                        m.visual.vertex_colors = np.tile(color, (len(m.vertices), 1))
                    else:
                        m.visual = trimesh.visual.ColorVisuals(m)
                        m.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(m.vertices), 1))
                else:
                    m.visual = trimesh.visual.ColorVisuals(m)
                    m.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(m.vertices), 1))
            else:
                if m.visual.vertex_colors.max() <= 1.0:
                    m.visual.vertex_colors = (m.visual.vertex_colors * 255).astype(np.uint8)
                else:
                    m.visual.vertex_colors = m.visual.vertex_colors.astype(np.uint8)
        except Exception as e:
            raise ValueError(f"Error processing vertex colors: {str(e)}")

    def _extract_colors_from_texture(self, m):
        try:
            material = m.visual.material
            image = material.baseColorTexture
            if image is not None:
                image_data = np.array(image)
                if image_data.dtype != np.uint8:
                    image_data = (np.clip(image_data, 0, 1) * 255).astype(np.uint8)

                uvs = m.visual.uv
                uvs = np.clip(uvs, 0, 1)
                h, w = image_data.shape[0], image_data.shape[1]
                i = ((1 - uvs[:, 1]) * (h - 1)).astype(int)
                j = (uvs[:, 0] * (w - 1)).astype(int)
                i = np.clip(i, 0, h - 1)
                j = np.clip(j, 0, w - 1)
                colors = image_data[i, j, :4]
                m.visual = trimesh.visual.ColorVisuals(m)
                m.visual.vertex_colors = colors
            else:
                m.visual = trimesh.visual.ColorVisuals(m)
                m.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(m.vertices), 1))
        except Exception as e:
            raise ValueError(f"Error extracting colors from texture: {str(e)}")

    def _send_to_td(self, mesh, broadcast):
        try:
            if not hasattr(mesh.visual, 'vertex_colors') or mesh.visual.vertex_colors is None:
                colors = np.tile([200, 200, 200, 255], (len(mesh.vertices), 1)).astype(np.uint8)
            else:
                colors = mesh.visual.vertex_colors.astype(np.uint8)

            header = [
                "ply",
                "format binary_little_endian 1.0",
                f"element vertex {len(mesh.vertices)}",
                "property float x",
                "property float y",
                "property float z",
                "property uchar red",
                "property uchar green",
                "property uchar blue",
                "property uchar alpha",
                "end_header\n"
            ]
            header = '\n'.join(header).encode('ascii')

            vertices = mesh.vertices.astype('<f4')
            colors = colors[:, :4].astype(np.uint8)

            vertex_count = len(vertices)
            binary_data = bytearray()
            for i in range(vertex_count):
                binary_data.extend(struct.pack('<fff', vertices[i, 0], vertices[i, 1], vertices[i, 2]))
                binary_data.extend(colors[i, :4].tobytes())

            buffer = io.BytesIO()
            buffer.write(header)
            buffer.write(binary_data)
            binary_output = buffer.getvalue()
            buffer.close()

            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(1000, binary_output, sid=sid)

            return {"ui": {
                "mesh": [{
                    "source": "websocket",
                    "content-type": "model/ply",
                    "type": "output",
                }]
            }}
        except Exception as e:
            raise ValueError(f"Error sending mesh: {str(e)}")


class ImagetoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_images(self, images, broadcast):
        results = []
        for tensor in images:
            array = 255.0 * tensor.cpu().numpy()
            image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))

            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(
                BinaryEventTypes.UNENCODED_PREVIEW_IMAGE,
                ["PNG", image, None],
                sid,
            )
            results.append({
                "source": "websocket",
                "content-type": "image/png",
                "type": "output",
            })

        return {"ui": {"images": results}}


class Comfy3DPacktoTD:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mesh": ("MESH",),
                "broadcast": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "send_to_td"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_to_td(self, mesh, broadcast):
        try:
            vertices = mesh.v.cpu().numpy().astype(np.float32)
            colors = None
            color_source = "none"

            if hasattr(mesh, 'albedo') and mesh.albedo is not None:
                albedo = mesh.albedo
                if hasattr(albedo, 'cpu'):
                    albedo = albedo.cpu()
                if hasattr(albedo, 'numpy'):
                    albedo = albedo.numpy()

                if len(albedo.shape) > 1:
                    if hasattr(mesh, 'vt') and mesh.vt is not None:
                        uvs = mesh.vt.cpu().numpy()
                        uvs = np.clip(uvs, 0, 1)
                        tex_h, tex_w = albedo.shape[:2]
                        
                        # 使用不翻转V的映射方法
                        mapped_u, mapped_v = uvs[:, 0], uvs[:, 1]
                        
                        # 使用双线性插值
                        tex_x = mapped_u * (tex_w - 1)
                        tex_y = mapped_v * (tex_h - 1)
                        
                        # 获取整数部分和小数部分
                        tex_x0 = np.floor(tex_x).astype(np.int32)
                        tex_y0 = np.floor(tex_y).astype(np.int32)
                        tex_x1 = np.minimum(tex_x0 + 1, tex_w - 1)
                        tex_y1 = np.minimum(tex_y0 + 1, tex_h - 1)
                        
                        # 计算权重
                        wx = tex_x - tex_x0
                        wy = tex_y - tex_y0
                        
                        # 双线性插值
                        c00 = albedo[tex_y0, tex_x0]
                        c01 = albedo[tex_y0, tex_x1]
                        c10 = albedo[tex_y1, tex_x0]
                        c11 = albedo[tex_y1, tex_x1]
                        
                        c0 = c00 * (1 - wx[:, np.newaxis]) + c01 * wx[:, np.newaxis]
                        c1 = c10 * (1 - wx[:, np.newaxis]) + c11 * wx[:, np.newaxis]
                        colors = c0 * (1 - wy[:, np.newaxis]) + c1 * wy[:, np.newaxis]
                        
                        color_source = "albedo_with_uv_no_v_flip"
                    else:
                        if albedo.shape[0] == len(vertices):
                            colors = albedo
                            color_source = "albedo_direct"
                else:
                    colors = albedo
                    color_source = "albedo_scalar"

            if colors is None and hasattr(mesh, 'vc') and mesh.vc is not None:
                colors = mesh.vc.cpu().numpy()
                color_source = "vertex_colors"

            if colors is None:
                positions = vertices - vertices.min(axis=0)
                positions = positions / positions.max(axis=0) if positions.max() > 0 else positions
                colors = positions
                color_source = "generated"

            # 确保颜色值在合理范围内
            if colors is not None:
                if colors.max() <= 1.0:
                    colors = (colors * 255).astype(np.uint8)
                else:
                    colors = np.clip(colors, 0, 255).astype(np.uint8)

            # 确保有Alpha通道
            if colors.shape[1] == 3:
                alpha = np.full((len(vertices), 1), 255, dtype=np.uint8)
                colors = np.concatenate([colors, alpha], axis=1)

            header = [
                "ply",
                "format binary_little_endian 1.0",
                f"element vertex {len(vertices)}",
                "property float x",
                "property float y",
                "property float z",
                "property uchar red",
                "property uchar green",
                "property uchar blue",
                "property uchar alpha",
                "end_header\n"
            ]
            header = '\n'.join(header).encode('ascii')

            binary_data = bytearray()
            for i in range(len(vertices)):
                binary_data.extend(struct.pack('<fff',
                    float(vertices[i, 0]), float(vertices[i, 1]), float(vertices[i, 2])))
                binary_data.extend(bytes([
                    int(colors[i, 0]),
                    int(colors[i, 1]),
                    int(colors[i, 2]),
                    int(colors[i, 3])
                ]))

            buffer = io.BytesIO()
            buffer.write(header)
            buffer.write(binary_data)
            binary_output = buffer.getvalue()
            buffer.close()

            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(1000, binary_output, sid=sid)

            return {"ui": {
                "mesh": [{
                    "source": "websocket",
                    "content-type": "model/ply",
                    "type": "output",
                }]
            }}

        except Exception as e:
            print(f"[Error] send_to_td: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Error sending mesh: {str(e)}")
                
class LoadTDImage:
    #This node originates from the comfyui-tooling-nodes and utilizes the "Load Image (Base64)" functionality.
    #https://github.com/Acly/comfyui-tooling-nodes
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ("IMAGE", "MASK")
    CATEGORY = "external_tooling"
    FUNCTION = "load_image"

    def load_image(self, image):
        try:
            imgdata = base64.b64decode(image)
            img = Image.open(BytesIO(imgdata))
            
            width, height = img.size
            
            if "A" in img.getbands():
                mask = np.array(img.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((height, width), dtype=torch.float32, device="cpu")
            
            if len(mask.shape) == 2:
                mask = mask.unsqueeze(0)
            
            img = img.convert("RGB")
            img = np.array(img).astype(np.float32) / 255.0
            img = torch.from_numpy(img)[None,]
            
            print(f"Image shape: {img.shape}, Mask shape: {mask.shape}")
            
            return (img, mask)
            
        except Exception as e:
            print(f"Error in LoadTDImage: {str(e)}")
            default_img = torch.zeros((1, 3, 64, 64), dtype=torch.float32, device="cpu")
            default_mask = torch.zeros((1, 64, 64), dtype=torch.float32, device="cpu")
            return (default_img, default_mask)
