import sys
import os
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QComboBox, QPushButton, QLabel, QProgressBar, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal

# Настройка сервера - измените этот адрес на нужный
SERVER_URL = "http://example.com:8000/"

class ModSyncWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal()

    def __init__(self, modpack_name, minecraft_path):
        super().__init__()
        self.modpack_name = modpack_name
        self.minecraft_path = minecraft_path

    def run(self):
        try:
            # Получаем информацию о сборке с сервера
            response = requests.get(f"{SERVER_URL}/modpack/{self.modpack_name}")
            modpack_info = response.json()

            # Создаем необходимые директории
            mods_path = os.path.join(self.minecraft_path, "mods")
            resourcepacks_path = os.path.join(self.minecraft_path, "resourcepacks")
            os.makedirs(mods_path, exist_ok=True)
            os.makedirs(resourcepacks_path, exist_ok=True)

            total_files = 0
            files_processed = 0

            # Синхронизация модов
            server_mods = set(modpack_info["mods"])
            local_mods = set(f for f in os.listdir(mods_path) if f.endswith('.jar'))

            # Переименовываем лишние моды
            for mod in local_mods - server_mods:
                if not mod.endswith('_'):
                    old_path = os.path.join(mods_path, mod)
                    new_path = os.path.join(mods_path, f"{mod}_")
                    os.rename(old_path, new_path)

            # Подсчитываем общее количество файлов для загрузки
            mods_to_download = server_mods - local_mods
            total_files += len(mods_to_download)

            # Синхронизация ресурспаков
            server_resourcepacks = set(modpack_info["resourcepacks"])
            local_resourcepacks = set(os.listdir(resourcepacks_path))

            # Переименовываем лишние ресурспаки
            for pack in local_resourcepacks - server_resourcepacks:
                if not pack.endswith('_'):
                    old_path = os.path.join(resourcepacks_path, pack)
                    new_path = os.path.join(resourcepacks_path, f"{pack}_")
                    os.rename(old_path, new_path)

            # Подсчитываем ресурспаки для загрузки
            resourcepacks_to_download = server_resourcepacks - local_resourcepacks
            total_files += len(resourcepacks_to_download)

            if total_files == 0:
                self.status.emit("Все файлы уже синхронизированы")
                self.progress.emit(100)
                self.finished.emit()
                return

            # Скачиваем недостающие моды
            for mod in mods_to_download:
                self.status.emit(f"Скачивание мода: {mod}")
                response = requests.get(
                    f"{SERVER_URL}/download/{self.modpack_name}/mods/{mod}",
                    stream=True
                )
                if response.status_code == 200:
                    with open(os.path.join(mods_path, mod), 'wb') as f:
                        f.write(response.content)
                    files_processed += 1
                    self.progress.emit(int(files_processed / total_files * 100))

            # Скачиваем недостающие ресурспаки
            for pack in resourcepacks_to_download:
                self.status.emit(f"Скачивание ресурспака: {pack}")
                response = requests.get(
                    f"{SERVER_URL}/download/{self.modpack_name}/resourcepacks/{pack}",
                    stream=True
                )
                if response.status_code == 200:
                    with open(os.path.join(resourcepacks_path, pack), 'wb') as f:
                        f.write(response.content)
                    files_processed += 1
                    self.progress.emit(int(files_processed / total_files * 100))

            self.status.emit("Синхронизация завершена")
            self.finished.emit()

        except Exception as e:
            self.status.emit(f"Ошибка: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Mod Sync")
        self.setMinimumWidth(400)

        # Создаем центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем элементы интерфейса
        self.modpack_combo = QComboBox()
        self.refresh_button = QPushButton("Обновить список сборок")
        self.minecraft_path_button = QPushButton("Выбрать папку Minecraft")
        self.sync_button = QPushButton("Синхронизировать")
        
        self.progress = QProgressBar()
        self.status_label = QLabel()

        # Добавляем элементы в layout
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.modpack_combo)
        layout.addWidget(self.minecraft_path_button)
        layout.addWidget(self.sync_button)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        # Подключаем сигналы
        self.refresh_button.clicked.connect(self.refresh_modpacks)
        self.minecraft_path_button.clicked.connect(self.select_minecraft_path)
        self.sync_button.clicked.connect(self.start_sync)

        self.minecraft_path = ""
        self.refresh_modpacks()

    def refresh_modpacks(self):
        try:
            response = requests.get(f"{SERVER_URL}/modpacks")
            modpacks = response.json()["modpacks"]
            self.modpack_combo.clear()
            self.modpack_combo.addItems(modpacks)
        except Exception as e:
            self.status_label.setText(f"Ошибка при получении списка сборок: {str(e)}")

    def select_minecraft_path(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку Minecraft")
        if path:
            self.minecraft_path = path
            self.minecraft_path_button.setText(f"Папка Minecraft: {os.path.basename(path)}")

    def start_sync(self):
        if not self.minecraft_path:
            self.status_label.setText("Выберите папку Minecraft!")
            return

        self.sync_button.setEnabled(False)
        self.worker = ModSyncWorker(
            self.modpack_combo.currentText(),
            self.minecraft_path
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.start()

    def on_sync_finished(self):
        self.sync_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 
