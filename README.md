# ComfyUI-TD

本节点实现了 TouchDesigner（以下简称 "TD"）与 ComfyUI 之间的无缝数据交互。

支持将ComfyUI生成的图像、视频、3D模型(点云)数据实时传输进TD。

---

## 用户须知
- **ComfyUI-TD** 的部分节点基于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main)进行了移植和优化。
- **ComfyUI-TD** 需与 **ComfyUI2TD.tox** 组件配合使用（插件已上传至`tox`文件夹）。  
- 请确保**ComfyUI2TD.tox** 组件版本更新至 **v_5.1.x** 或更高版本。此版本对组件代码进行了全面重构，支持了视频与3D模型(点云)的数据传输。另重写了WebSocket接口，有效解决了在网络条件较差时，使用云端ComfyUI可能出现的数据（图像）无法正常返回的问题。   
- **ComfyUI2TD.tox** 组件至 **v_5.1.x** 版本起，预置的工作流将使用ComfyUI-TD节点，不再使用于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main)。
- 旧版 **ComfyUI2TD.tox** 组件基于[TDComfyUI](https://github.com/olegchomp/TDComfyUI)项目开发，感谢olegchomp！
- 若需使用云端ComfyUI，可选择[仙宫云](https://github.com/Acly/comfyui-tooling-nodes/tree/main)服务器，配套镜像已准备完毕。
  
---


## 使用说明
### 视频教程
- 请按照顺序观看以下视频。
- [1. ComfyUI2TD插件 基础使用教程](https://github.com/Acly/comfyui-tooling-nodes/tree/main)
- [2. 云端仙宫云 使用教程](https://github.com/Acly/comfyui-tooling-nodes/tree/main)
- [3. ComfyUI2TD_v 5.1 新版教程](https://github.com/Acly/comfyui-tooling-nodes/tree/main)

---

### ComfyUI-TD节点安装 
#### 方法一：  
- 使用[ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager?tab=readme-ov-file)搜索**ComfyUI-TD**，并直接进行节点安装。  

#### 方法二：  
- 手动安装：将本项目下载后解压放置于`X:\ComfyUI_windows_portable\ComfyUI\custom_nodes`。

#### 方法三： 
- 使用git clone命令进行安装。
```
cd custom_nodes
git clone https://github.com/JiSenHua/ComfyUI-TD.git
```
#### 方法四：  
- 配合**ComfyUI2TD.tox**组件，使用`InjectFile 注入插件`功能，将节点自动注入至`X:\ComfyUI_windows_portable\ComfyUI\custom_nodes`。

---

## ComfyUI-TD节点说明 

### Hy3DtoTD

- 本节点支持将**Hunyuan3D_V2 混元V2**生成的GLB模型转换为点云数据，并返回至 **TD** 进行解析，从而生成对应的CHOP组件。
- 使用本节点需安装[ComfyUI-Hunyuan3DWrapper](https://github.com/kijai/ComfyUI-Hunyuan3DWrapper)节点。  
- 若安装[ComfyUI-Hunyuan3DWrapper](https://github.com/kijai/ComfyUI-Hunyuan3DWrapper)遇到困难，可选择使用云端**仙宫云**镜像。  
- **ComfyUI2TD.tox** 预置的工作流 **Hunyuan3DV2_PointCloud** 提供了此节点的基础用法示例，对应的`.js`工作流文件已上传至`workflow`文件夹。
- 最新的[ComfyUI-Hunyuan3DWrapper](https://github.com/kijai/ComfyUI-Hunyuan3DWrapper)已将所有模型工作流改为`trimesh`。
- `broadcast`广播参数（默认关闭）：启用该参数后，生成的点云数据将广播至所有已建立 WebSocket 连接的客户端。

### Tripo3DtoTD

- 本节点支持将**Tripo3D**生成的GLB模型转换为点云数据，并返回至 **TD** 进行解析，从而生成对应的CHOP组件。
- 使用本节点需安装[ComfyUI-Tripo](https://github.com/VAST-AI-Research/ComfyUI-Tripo)节点。  
- Tripo本非开源模型，需要进入[Tripo 官网](https://platform.tripo3d.ai/) 注册账户并申请API。
- **ComfyUI2TD.tox** 预置的工作流 **Tripo3D_PointCloud** 提供了此节点的基础用法示例，对应的`.js`工作流文件已上传至`workflow`文件夹。
- `broadcast`广播参数（默认关闭）：启用该参数后，生成的点云数据将广播至所有已建立 WebSocket 连接的客户端。

### Comfy3DPacktoTD

- 本节点支持将**3DPack**生成的GLB模型转换为点云数据，并返回至 **TD** 进行解析，从而生成对应的CHOP组件。
- 使用本节点需安装[ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack)节点。  
- 若安装[ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack)遇到困难，可选择使用云端**仙宫云**镜像。
- **ComfyUI2TD.tox** 预置的工作流 **3DPack_xxx_PointCloud** 提供了此节点的基础用法示例，对应的`.js`工作流文件已上传至`workflow`文件夹。
- **3DPack**中的**Hunyuan3D_V2**与**Hunyuan3DWrapper**并不互通，请确保使用各自对应的传输节点
- `broadcast`广播参数（默认关闭）：启用该参数后，生成的点云数据将广播至所有已建立 WebSocket 连接的客户端。
- **注意**：目前仙宫云端镜像仅对**TRELLIS**、**Hunyuan3D_V2**和**StableFast3D**进行了测试。其他3D模型尚未验证，如遇问题请在Issues中反馈。

### ImagetoTD

- 基于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main) **Send Image (WebSocket)** 节点二次开发。
- 本节点支持将ComfyUI生成的图片返回至 **TD** 进行解析，从而生成对应的TOP组件。
- `broadcast`广播参数（默认关闭）：启用该参数后，生成的点云数据将广播至所有已建立 WebSocket 连接的客户端。
- **ComfyUI2TD.tox**组件至 **v_5.1.x** 版本起，预置的工作流将使用ComfyUI-TD节点，不再使用于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main)。

### LoadTDImage

- 基于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main) **Load Image (Base64)** 节点移植。
- 本节点支持由TD发送的TOP元件作为图像输入源发送给ComfyUI。
- **ComfyUI2TD.tox**组件至 **v_5.1.x** 版本起，预置的工作流将使用ComfyUI-TD节点，不再使用于[ComfyUI-Tooling-Nodes](https://github.com/Acly/comfyui-tooling-nodes/tree/main)。

