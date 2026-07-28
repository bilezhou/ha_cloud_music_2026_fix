from pathlib import Path

from homeassistant.util.json import load_json


def custom_components_path(file_path: str) -> str:
    """返回相对于当前组件目录的路径，不依赖 Home Assistant 工作目录。"""
    return str(Path(__file__).resolve().parent.parent / file_path)


class Manifest:

    def __init__(self, domain):
        self.domain = domain
        self.manifest_path = custom_components_path(f"{domain}/manifest.json")
        self.update()

    @property
    def remote_url(self):
        return "https://gitee.com/shaonianzhentan/ha_cloud_music/raw/dev/custom_components/ha_cloud_music/manifest.json"

    def update(self):
        data = load_json(self.manifest_path, {})
        self.domain = data.get("domain")
        self.name = data.get("name")
        self.version = data.get("version")
        self.documentation = data.get("documentation")


manifest = Manifest("ha_cloud_music")

