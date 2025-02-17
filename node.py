import trimesh
import numpy as np
import io
from server import PromptServer, BinaryEventTypes
from pathlib import Path
from PIL import Image

class Hy3DtoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trimesh": ("TRIMESH",),
                "broadcast": ("BOOLEAN", {"default": False}),  # 添加broadcast参数
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_mesh"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_mesh(self, trimesh, broadcast):  # 添加broadcast参数
        # 处理mesh数据，确保正确的格式和颜色信息
        processed_mesh = self.process_mesh(trimesh)
        
        try:
            # 使用BytesIO直接在内存中处理数据
            buffer = io.BytesIO()
            processed_mesh.export(file_obj=buffer, file_type='ply')
            binary_data = buffer.getvalue()
            buffer.close()
            
            # 发送数据到TouchDesigner
            server = PromptServer.instance
            sid = None if broadcast else server.client_id  # 根据broadcast设置sid
            server.send_sync(1000, binary_data, sid=sid)

            return {"ui": {
                "mesh": [{
                    "source": "websocket",
                    "content-type": "model/ply",
                    "type": "output",
                }]
            }}
            
        except Exception as e:
            print(f"发送mesh时出错: {str(e)}")
            raise

    def process_mesh(self, mesh):
        """处理mesh数据，确保正确处理颜色信息"""
        try:
            if isinstance(mesh, (str, Path)):
                mesh = trimesh.load(mesh)
            
            if isinstance(mesh, trimesh.Scene):
                # 将场景中的所有mesh合并为一个
                meshes = []
                for m in mesh.geometry.values():
                    if isinstance(m, trimesh.Trimesh):
                        meshes.append(m)
                if meshes:
                    mesh = trimesh.util.concatenate(meshes)
                else:
                    raise ValueError("没有找到有效的mesh数据")

            # 确保mesh是Trimesh对象
            if not isinstance(mesh, trimesh.Trimesh):
                raise ValueError("输入数据不是有效的Trimesh对象")

            # 修复法线
            mesh.fix_normals()

            # 处理颜色信息
            if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
                # 如果有UV贴图，转换为顶点颜色
                mesh.visual = mesh.visual.to_color()
            
            # 如果没有顶点颜色，添加默认颜色
            if not hasattr(mesh.visual, 'vertex_colors') or mesh.visual.vertex_colors is None:
                mesh.visual = trimesh.visual.ColorVisuals(mesh)
                mesh.visual.vertex_colors = np.tile([200, 200, 200, 255], (len(mesh.vertices), 1))

            return mesh
            
        except Exception as e:
            print(f"处理mesh时出错: {str(e)}")
            raise

class ImagetoTD:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "format": (["PNG", "JPEG"], {"default": "PNG"}),
                "broadcast": ("BOOLEAN", {"default": False}), 
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "send_images"
    OUTPUT_NODE = True
    CATEGORY = "TouchDesigner"

    def send_images(self, images, format, broadcast):
        results = []
        for tensor in images:
            array = 255.0 * tensor.cpu().numpy()
            image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8))

            server = PromptServer.instance
            sid = None if broadcast else server.client_id  # 根据选项设置 sid
            server.send_sync(
                BinaryEventTypes.UNENCODED_PREVIEW_IMAGE,
                [format, image, None],  # 第三个参数始终为 None
                sid,  # 使用 sid 作为发送目标
            )
            results.append({
                "source": "websocket",
                "content-type": f"image/{format.lower()}",
                "type": "output",
            })

        return {"ui": {"images": results}}
