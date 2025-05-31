from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
from typing import List, Dict
import json

app = FastAPI()

class ModManager:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.modpacks_path = os.path.join(base_path, "modpacks")
        self._ensure_directories()

    def _ensure_directories(self):
        """Создает необходимые директории, если они не существуют"""
        os.makedirs(self.modpacks_path, exist_ok=True)

    def get_modpack_list(self) -> List[str]:
        """Возвращает список доступных сборок"""
        return [d for d in os.listdir(self.modpacks_path) 
                if os.path.isdir(os.path.join(self.modpacks_path, d))]

    def get_modpack_info(self, modpack_name: str) -> Dict:
        """Возвращает информацию о конкретной сборке"""
        modpack_path = os.path.join(self.modpacks_path, modpack_name)
        mods_path = os.path.join(modpack_path, "mods")
        resourcepacks_path = os.path.join(modpack_path, "resourcepacks")
        
        mods = []
        resourcepacks = []
        
        if os.path.exists(mods_path):
            mods = [f for f in os.listdir(mods_path) if f.endswith('.jar')]
        
        if os.path.exists(resourcepacks_path):
            resourcepacks = os.listdir(resourcepacks_path)
            
        return {
            "name": modpack_name,
            "mods": mods,
            "resourcepacks": resourcepacks
        }

mod_manager = ModManager("minecraft_server")

@app.get("/modpacks")
async def get_modpacks():
    """Получить список всех доступных сборок"""
    return {"modpacks": mod_manager.get_modpack_list()}

@app.get("/modpack/{modpack_name}")
async def get_modpack(modpack_name: str):
    """Получить информацию о конкретной сборке"""
    return mod_manager.get_modpack_info(modpack_name)

@app.get("/download/{modpack_name}/{file_type}/{filename}")
async def download_file(modpack_name: str, file_type: str, filename: str):
    """Скачать мод или ресурспак"""
    base_path = os.path.join(mod_manager.modpacks_path, modpack_name)
    file_path = os.path.join(base_path, file_type, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    # Настройки сервера
    SERVER_HOST = "0.0.0.0"  # Можно изменить на конкретный IP
    SERVER_PORT = 8000       # Можно изменить порт
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT) 