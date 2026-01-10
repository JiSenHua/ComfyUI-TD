import struct
import numpy as np
import io
from server import PromptServer, BinaryEventTypes
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import torch
import tempfile
import os


class Hy3DtoTD:
    #https://github.com/kijai/ComfyUI-Hunyuan3DWrapper
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
        try:
            processed_mesh = self.process_mesh(trimesh)
            return self._send_to_td(processed_mesh, broadcast)
        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def process_mesh(self, mesh):
        try:
            import trimesh

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

        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def _send_to_td(self, mesh, broadcast):
        try:
            import trimesh

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
        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
        except Exception as e:
            raise ValueError(f"Error sending mesh to TouchDesigner: {str(e)}")


class Tripo3DtoTD:
    #https://github.com/VAST-AI-Research/ComfyUI-Tripo
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
        try:
            processed_mesh = self.process_mesh(model_file)
            return self._send_to_td(processed_mesh, broadcast)
        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def process_mesh(self, model_file):
        try:
            import trimesh
            if not model_file.startswith(('http://', 'https://')) and not os.path.isabs(model_file):
                try:
                    import folder_paths
                    output_dir = folder_paths.get_output_directory()
                    local_path = os.path.join(output_dir, model_file)
                    if os.path.exists(local_path):
                        model_file = local_path
                except:
                    pass

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

        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
        except Exception as e:
            raise ValueError(f"Error processing mesh: {str(e)}")

    def _process_vertex_colors(self, m):
        try:
            import trimesh

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
        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
        except Exception as e:
            raise ValueError(f"Error processing vertex colors: {str(e)}")

    def _extract_colors_from_texture(self, m):
        try:
            import trimesh

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
        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
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
        except ImportError:
            raise ImportError("Please install the trimesh library: pip install trimesh")
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


class ImagetoTD_JPEG:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "broadcast": ("BOOLEAN", {"default": False}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_images(self, images, broadcast, quality):
        import numpy as np
        from PIL import Image
        import io
        import struct

        results = []
        for tensor in images:
            array = 255.0 * tensor.cpu().numpy()
            image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))

            bytesIO = io.BytesIO()
            type_num = 1
            header = struct.pack(">I", type_num)
            bytesIO.write(header)

            image.save(bytesIO, format="JPEG", quality=quality)
            jpeg_bytes = bytesIO.getvalue()

            server = PromptServer.instance
            sid = None if broadcast else server.client_id

            server.send_sync(
                BinaryEventTypes.PREVIEW_IMAGE,
                jpeg_bytes,
                sid,
            )
            results.append({
                "source": "websocket",
                "content-type": "image/jpeg",
                "type": "output",
            })

        return {"ui": {"images": results}}

class Comfy3DPacktoTD:
    #https://github.com/MrForExample/ComfyUI-3D-Pack
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

                        mapped_u, mapped_v = uvs[:, 0], uvs[:, 1]

                        tex_x = mapped_u * (tex_w - 1)
                        tex_y = mapped_v * (tex_h - 1)

                        tex_x0 = np.floor(tex_x).astype(np.int32)
                        tex_y0 = np.floor(tex_y).astype(np.int32)
                        tex_x1 = np.minimum(tex_x0 + 1, tex_w - 1)
                        tex_y1 = np.minimum(tex_y0 + 1, tex_h - 1)

                        wx = tex_x - tex_x0
                        wy = tex_y - tex_y0

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

            if colors is not None:
                if colors.max() <= 1.0:
                    colors = (colors * 255).astype(np.uint8)
                else:
                    colors = np.clip(colors, 0, 255).astype(np.uint8)

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


class TripoSRtoTD:
    #https://github.com/flowtyone/ComfyUI-Flowty-TripoSR
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
            if isinstance(mesh, list):
                if len(mesh) > 0:
                    mesh_obj = mesh[0]
                else:
                    raise ValueError("Empty mesh list received")
            else:
                mesh_obj = mesh

            if hasattr(mesh_obj, 'vertices'):
                vertices = mesh_obj.vertices
                if hasattr(vertices, 'cpu'):
                    vertices = vertices.cpu()
                if hasattr(vertices, 'numpy'):
                    vertices = vertices.numpy()
                vertices = vertices.astype(np.float32)
            else:
                raise ValueError("Cannot find vertex data in mesh object")

            rotated_vertices = vertices.copy()
            rotated_vertices[:, 0] = -vertices[:, 0]
            rotated_vertices[:, 1], rotated_vertices[:, 2] = vertices[:, 2], vertices[:, 1]

            final_vertices = rotated_vertices.copy()
            final_vertices[:, 0] = rotated_vertices[:, 2]
            final_vertices[:, 2] = -rotated_vertices[:, 0]

            vertices = final_vertices

            colors = None

            if hasattr(mesh_obj, 'visual') and mesh_obj.visual is not None:
                visual = mesh_obj.visual

                if hasattr(visual, 'vertex_colors') and visual.vertex_colors is not None:
                    colors = visual.vertex_colors
                    if hasattr(colors, 'cpu'):
                        colors = colors.cpu()
                    if hasattr(colors, 'numpy'):
                        colors = colors.numpy()

                elif hasattr(visual, 'face_colors') and visual.face_colors is not None:
                    face_colors = visual.face_colors
                    if hasattr(face_colors, 'cpu'):
                        face_colors = face_colors.cpu()
                    if hasattr(face_colors, 'numpy'):
                        face_colors = face_colors.numpy()

                    if hasattr(mesh_obj, 'faces') and mesh_obj.faces is not None:
                        faces = mesh_obj.faces
                        if hasattr(faces, 'cpu'):
                            faces = faces.cpu()
                        if hasattr(faces, 'numpy'):
                            faces = faces.numpy()

                        colors = np.zeros((len(vertices), 4), dtype=np.uint8)
                        vertex_color_count = np.zeros(len(vertices), dtype=np.int32)

                        for i, face in enumerate(faces):
                            for vertex_idx in face:
                                colors[vertex_idx] += face_colors[i]
                                vertex_color_count[vertex_idx] += 1

                        for i in range(len(vertices)):
                            if vertex_color_count[i] > 0:
                                colors[i] = colors[i] // vertex_color_count[i]

                elif hasattr(visual, 'material') and visual.material is not None:
                    material = visual.material

                    if hasattr(material, 'diffuse') and material.diffuse is not None:
                        diffuse = material.diffuse
                        colors = np.tile(diffuse, (len(vertices), 1))

            if colors is None and hasattr(mesh_obj, '_visual') and mesh_obj._visual is not None:
                visual = mesh_obj._visual

                if hasattr(visual, 'vertex_colors') and visual.vertex_colors is not None:
                    colors = visual.vertex_colors
                    if hasattr(colors, 'cpu'):
                        colors = colors.cpu()
                    if hasattr(colors, 'numpy'):
                        colors = colors.numpy()

            if colors is None and hasattr(mesh_obj, 'visual') and hasattr(mesh_obj.visual,
                                                                          'uv') and mesh_obj.visual.uv is not None:
                if hasattr(mesh_obj.visual, 'material') and hasattr(mesh_obj.visual.material, 'image'):
                    uvs = mesh_obj.visual.uv
                    image = mesh_obj.visual.material.image

                    h, w = image.shape[:2]
                    u = np.clip(uvs[:, 0], 0, 1) * (w - 1)
                    v = np.clip(uvs[:, 1], 0, 1) * (h - 1)

                    u_int = np.round(u).astype(np.int32)
                    v_int = np.round(v).astype(np.int32)

                    u_int = np.clip(u_int, 0, w - 1)
                    v_int = np.clip(v_int, 0, h - 1)

                    colors = image[v_int, u_int]

            if colors is None:
                np.random.seed(42)
                colors = np.random.randint(100, 200, size=(len(vertices), 3), dtype=np.uint8)
                alpha = np.full((len(vertices), 1), 255, dtype=np.uint8)
                colors = np.concatenate([colors, alpha], axis=1)

            if colors is not None:
                if len(colors.shape) == 1:
                    colors = np.column_stack([colors, colors, colors])

                if colors.max() <= 1.0 and colors.dtype != np.uint8:
                    colors = (colors * 255).astype(np.uint8)
                else:
                    colors = np.clip(colors, 0, 255).astype(np.uint8)

                if colors.shape[1] == 3:
                    alpha = np.full((len(vertices), 1), 255, dtype=np.uint8)
                    colors = np.concatenate([colors, alpha], axis=1)
                elif colors.shape[1] > 4:
                    colors = colors[:, :4]

                if len(colors) != len(vertices):
                    if len(colors) > len(vertices):
                        colors = colors[:len(vertices)]
                    else:
                        last_color = colors[-1]
                        padding = np.tile(last_color, (len(vertices) - len(colors), 1))
                        colors = np.vstack([colors, padding])

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
            import traceback
            traceback.print_exc()
            raise ValueError(f"Error sending mesh: {str(e)}")


class LoadTDImage:
    # This node originates from the comfyui-tooling-nodes and utilizes the "Load Image (Base64)" functionality.
    # https://github.com/Acly/comfyui-tooling-nodes
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("STRING", {"multiline": False})}}

    RETURN_TYPES = ("IMAGE", "MASK")
    CATEGORY = "TouchDesigner"
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


class VideotoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "frame_rate": ("FLOAT", {"default": 8, "min": 1, "step": 1}),
                "quality": ("INT", {"default": 75, "min": 15, "max": 100, "step": 1}),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "process_video"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def process_video(self, images, frame_rate, broadcast, quality):
        if images is None or (isinstance(images, torch.Tensor) and images.size(0) == 0):
            raise ValueError("No valid images provided")

        video_binary = self._encode_video_ffmpeg(images, frame_rate, quality)

        return self._send_to_td(video_binary, broadcast)

    def _encode_video_ffmpeg(self, images, frame_rate, quality):
        try:
            import imageio_ffmpeg

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name

            if isinstance(images, torch.Tensor):
                if len(images.shape) != 4:
                    raise ValueError(f"Expected 4D tensor, got shape {images.shape}")

                images_np = images.cpu().numpy()
                if images_np.max() <= 1.0:
                    images_np = (images_np * 255).astype(np.uint8)
                else:
                    images_np = images_np.astype(np.uint8)
            else:
                raise TypeError("Images must be a torch.Tensor")

            height, width = images_np[0].shape[:2]

            output_params = [
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', str(51 - quality // 2),
                '-pix_fmt', 'yuv420p'
            ]

            writer = imageio_ffmpeg.write_frames(
                temp_path,
                (width, height),
                fps=frame_rate,
                output_params=output_params
            )

            writer.send(None)

            for img in images_np:
                if img.shape[2] == 4:  # RGBA
                    img = img[:, :, :3]

                if not img.flags['C_CONTIGUOUS']:
                    img = np.ascontiguousarray(img)

                writer.send(img)

            writer.close()

            with open(temp_path, 'rb') as f:
                video_binary = f.read()

            os.unlink(temp_path)

            return video_binary

        except Exception as e:
            raise RuntimeError(f"Error encoding video with ffmpeg: {str(e)}")

    def _send_to_td(self, video_binary, broadcast):
        try:
            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(1001, video_binary, sid=sid)

            return {"ui": {
                "video": [{
                    "source": "websocket",
                    "content-type": "video/mp4",
                    "type": "output",
                }]
            }}
        except Exception as e:
            raise ValueError(f"Error sending video: {str(e)}")

class AudiotoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio": ("AUDIO",),
                "format": (["mp3", "wav"],),
                "bitrate_kbps": ("INT", {"default": 192, "min": 32, "max": 512, "step": 16}),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "process_audio"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def process_audio(self, audio, format, bitrate_kbps, broadcast):
        if audio is None or not isinstance(audio, dict):
            raise ValueError("No valid audio dict provided")
        if "waveform" not in audio or "sample_rate" not in audio:
            raise ValueError("Audio dict must contain 'waveform' and 'sample_rate'")

        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])
        if not isinstance(waveform, torch.Tensor):
            raise TypeError("audio['waveform'] must be a torch.Tensor")
        if waveform.ndim != 3:
            raise ValueError(f"Expected waveform as 3D tensor [B, C, T], got shape {tuple(waveform.shape)}")
        if waveform.size(0) > 1:
            waveform = waveform[0:1, ...]
        waveform = waveform[0]

        with torch.no_grad():
            max_abs = waveform.abs().amax()
            if torch.isfinite(max_abs) and max_abs > 1.0:
                waveform = waveform / max_abs

        wav_np = waveform.detach().cpu().float().numpy()
        if wav_np.ndim != 2:
            raise ValueError(f"Waveform must be [C, T] after squeeze, got {wav_np.shape}")
        wav_np = np.transpose(wav_np, (1, 0))

        if format == "wav":
            audio_binary, content_type = self._encode_wav(wav_np, sample_rate)
        elif format == "mp3": 
            audio_binary, content_type = self._encode_mp3(wav_np, sample_rate, bitrate_kbps)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return self._send_to_td(audio_binary, content_type, broadcast)

    def _encode_wav(self, wav_np, sample_rate):
        import soundfile as sf
        buf = io.BytesIO()
        if wav_np.ndim == 1:
            wav_np = wav_np[:, None]
        sf.write(buf, wav_np, samplerate=sample_rate, subtype="PCM_16", format="WAV")
        audio_binary = buf.getvalue()
        buf.close()
        return audio_binary, "audio/wav"

    def _encode_mp3(self, wav_np, sample_rate, bitrate_kbps):  
        import imageio_ffmpeg, subprocess
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:  
            temp_path = temp_file.name
        try:
            channels = wav_np.shape[1] if wav_np.ndim == 2 else 1
            if wav_np.ndim == 1:
                wav_np = wav_np[:, None]
                channels = 1
            pcm = wav_np.astype(np.float32, copy=False)
            if not pcm.flags["C_CONTIGUOUS"]:
                pcm = np.ascontiguousarray(pcm)

            cmd = [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-y",
                "-f", "f32le",
                "-ac", str(channels),
                "-ar", str(sample_rate),
                "-i", "pipe:0",
                "-c:a", "libmp3lame", 
                "-b:a", f"{int(bitrate_kbps)}k",
                temp_path
            ]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.stdin.write(pcm.tobytes())
            proc.stdin.close()
            rc = proc.wait()
            if rc != 0:
                stderr = proc.stderr.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"ffmpeg failed (code {rc}): {stderr.strip()}")
            with open(temp_path, "rb") as f:
                audio_binary = f.read()
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        return audio_binary, "audio/mpeg"

    def _send_to_td(self, audio_binary, content_type, broadcast):
        server = PromptServer.instance
        sid = None if broadcast else server.client_id
        server.send_sync(1002, audio_binary, sid=sid)
        return {"ui": {
            "audio": [{
                "source": "websocket",
                "content-type": content_type,
                "type": "output",
            }]
        }}

class GaussianSplattingtoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ply_path": ("STRING",),
                "broadcast": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_gaussian_splatting"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_gaussian_splatting(self, ply_path, broadcast):
        try:
            gs_data = self.process_ply(ply_path)
            return self._send_to_td(gs_data, broadcast)
        except Exception as e:
            raise ValueError(f"Error processing Gaussian Splatting data: {str(e)}")

    def process_ply(self, ply_path):
        try:
            from plyfile import PlyData
            
            if not ply_path.startswith(('http://', 'https://')) and not os.path.isabs(ply_path):
                try:
                    import folder_paths
                    output_dir = folder_paths.get_output_directory()
                    local_path = os.path.join(output_dir, ply_path)
                    if os.path.exists(local_path):
                        ply_path = local_path
                except:
                    pass
            
            if not os.path.exists(ply_path):
                raise ValueError(f"PLY file not found: {ply_path}")
            
            plydata = PlyData.read(ply_path)
            vertex = plydata['vertex']
            
            required_props = ['x', 'y', 'z', 'f_dc_0', 'f_dc_1', 'f_dc_2', 
                            'opacity', 'scale_0', 'scale_1', 'scale_2', 
                            'rot_0', 'rot_1', 'rot_2', 'rot_3']
            
            missing_props = [prop for prop in required_props if prop not in vertex.data.dtype.names]
            if missing_props:
                raise ValueError(f"Missing properties in PLY file: {missing_props}")
            
            gs_data = {
                'positions': np.stack([vertex['x'], vertex['y'], vertex['z']], axis=1).astype(np.float32),
                'colors': np.stack([vertex['f_dc_0'], vertex['f_dc_1'], vertex['f_dc_2']], axis=1).astype(np.float32),
                'opacity': vertex['opacity'].astype(np.float32),
                'scales': np.stack([vertex['scale_0'], vertex['scale_1'], vertex['scale_2']], axis=1).astype(np.float32),
                'rotations': np.stack([vertex['rot_0'], vertex['rot_1'], vertex['rot_2'], vertex['rot_3']], axis=1).astype(np.float32),
            }
            
            return gs_data
            
        except ImportError:
            raise ImportError("Please install the plyfile library: pip install plyfile")
        except Exception as e:
            raise ValueError(f"Error reading PLY file: {str(e)}")

    def _send_to_td(self, gs_data, broadcast):
        try:
            num_points = len(gs_data['positions'])
            
            header = [
                "ply",
                "format binary_little_endian 1.0",
                f"element vertex {num_points}",
                "property float x",
                "property float y",
                "property float z",
                "property float f_dc_0",
                "property float f_dc_1",
                "property float f_dc_2",
                "property float opacity",
                "property float scale_0",
                "property float scale_1",
                "property float scale_2",
                "property float rot_0",
                "property float rot_1",
                "property float rot_2",
                "property float rot_3",
                "end_header\n"
            ]
            header = '\n'.join(header).encode('ascii')
            
            binary_data = bytearray()
            for i in range(num_points):
                binary_data.extend(struct.pack('<fff', 
                    gs_data['positions'][i, 0], 
                    gs_data['positions'][i, 1], 
                    gs_data['positions'][i, 2]))
                
                binary_data.extend(struct.pack('<fff', 
                    gs_data['colors'][i, 0], 
                    gs_data['colors'][i, 1], 
                    gs_data['colors'][i, 2]))
                
                binary_data.extend(struct.pack('<f', gs_data['opacity'][i]))
                
                binary_data.extend(struct.pack('<fff', 
                    gs_data['scales'][i, 0], 
                    gs_data['scales'][i, 1], 
                    gs_data['scales'][i, 2]))
                
                binary_data.extend(struct.pack('<ffff', 
                    gs_data['rotations'][i, 0], 
                    gs_data['rotations'][i, 1], 
                    gs_data['rotations'][i, 2], 
                    gs_data['rotations'][i, 3]))
            
            buffer = io.BytesIO()
            buffer.write(header)
            buffer.write(binary_data)
            binary_output = buffer.getvalue()
            buffer.close()
            
            server = PromptServer.instance
            sid = None if broadcast else server.client_id
            server.send_sync(1003, binary_output, sid=sid)
            
            return {"ui": {
                "gaussian_splatting": [{
                    "source": "websocket",
                    "content-type": "model/ply",
                    "type": "output",
                    "point_count": num_points,
                }]
            }}
            
        except Exception as e:
            raise ValueError(f"Error sending Gaussian Splatting data: {str(e)}")
