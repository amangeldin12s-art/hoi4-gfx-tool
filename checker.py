import os
import platform
import ctypes
import json
import math
import random
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QTreeWidget,
    QTreeWidgetItem, QSplitter, QFrame, QComboBox, QDialog,
    QSizePolicy, QMessageBox, QProgressBar,
    QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPoint, QEvent
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QCursor, QPolygon, QPainterPath
)
from PIL import Image, ImageDraw

# ====================== КОНФИГУРАЦИЯ ======================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_FILE = BASE_DIR / "config.json"

# --- ПОЛНЫЙ СЛОВАРЬ ЛОКАЛИЗАЦИИ ---
LANG = {
    "RU": {
        "title": "HOI4 GFX STUDIO", "base_mod": "Оригинальный мод:", "sub_mod": "Сабмод (Папка замены):",
        "browse": "Обзор...", "scan_btn": "⚡ Анализ GFX", "file_label": "Проводник GFX:",
        "search_hint": "Поиск...", "all_folders": "Все папки (Root)", "clear_btn": "✕",
        "back_btn": "◀ Назад", "theme_btn": "Тема", "orig_view": "ОРИГИНАЛ",
        "sub_view": "ЗАМЕНА", "not_found": "ФАЙЛ НЕ НАЙДЕН", "select_file": "Выберите файл",
        "start_replace": "▶  ЗАМЕНИТЬ / ДОБАВИТЬ", "success_title": "Успешно",
        "success_msg": "Файл успешно заменён!", "loading": "Загрузка...",
        "size_lbl": "Размер: ", "err_dir": "Ошибка: Сначала выберите папки!",
        "editor_title": "Редактор GFX", "editor_save": "✔ Применить и Сохранить", "editor_preset": "Формат / Пресет:",
        "btn_fit": "Вместить", "btn_fill": "Заполнить", "btn_stretch": "Растянуть",
        "zoom_lbl": "Зум: ", "img_missing": "ИЗОБРАЖЕНИЕ ОТСУТСТВУЕТ"
    },
    "EN": {
        "title": "HOI4 GFX STUDIO", "base_mod": "Original Mod:", "sub_mod": "Submod (Target Folder):",
        "browse": "Browse...", "scan_btn": "⚡ GFX Analysis", "file_label": "GFX Explorer:",
        "search_hint": "Search...", "all_folders": "All folders (Root)", "clear_btn": "✕",
        "back_btn": "◀ Back", "theme_btn": "Theme", "orig_view": "ORIGINAL",
        "sub_view": "REPLACEMENT", "not_found": "FILE NOT FOUND", "select_file": "Select a file",
        "start_replace": "▶  REPLACE / ADD", "success_title": "Success",
        "success_msg": "File replaced successfully!", "loading": "Loading...",
        "size_lbl": "Size: ", "err_dir": "Error: Select directories first!",
        "editor_title": "GFX Editor", "editor_save": "✔ Apply & Save", "editor_preset": "Format / Preset:",
        "btn_fit": "Fit", "btn_fill": "Fill", "btn_stretch": "Stretch",
        "zoom_lbl": "Zoom: ", "img_missing": "IMAGE MISSING"
    },
    "JA": {"title": "HOI4 GFX STUDIO", "base_mod": "元モッド:", "sub_mod": "サブモッド:", "browse": "参照...", "scan_btn": "⚡ 解析開始", "file_label": "エクスプローラー:", "search_hint": "検索...", "all_folders": "すべてのフォルダ", "clear_btn": "✕", "back_btn": "◀ 戻る", "theme_btn": "テーマ", "orig_view": "オリジナル", "sub_view": "置換", "not_found": "未検出", "select_file": "選択", "start_replace": "▶  開始", "success_title": "成功", "success_msg": "成功！", "loading": "読み込み...", "size_lbl": "サイズ: ", "err_dir": "エラー！", "btn_fit": "合わせる", "btn_fill": "埋める", "btn_stretch": "伸ばす", "zoom_lbl": "ズーム: ", "img_missing": "画像なし", "editor_title": "エディタ", "editor_save": "✔ 保存", "editor_preset": "プリセット:"},
    "KO": {"title": "HOI4 GFX STUDIO", "base_mod": "원본 모드:", "sub_mod": "서브모드:", "browse": "찾아보기...", "scan_btn": "⚡ 분석 시작", "file_label": "탐색기:", "search_hint": "검색...", "all_folders": "모든 폴더", "clear_btn": "✕", "back_btn": "◀ 뒤로", "theme_btn": "테마", "orig_view": "원본", "sub_view": "교체", "not_found": "찾을 수 없음", "select_file": "선택", "start_replace": "▶  시작", "success_title": "성공", "success_msg": "성공!", "loading": "로딩...", "size_lbl": "크기: ", "err_dir": "오류!", "btn_fit": "맞춤", "btn_fill": "채우기", "btn_stretch": "늘리기", "zoom_lbl": "확대: ", "img_missing": "이미지 없음", "editor_title": "에디터", "editor_save": "✔ 저장", "editor_preset": "프리셋:"},
    "DE": {"title": "HOI4 GFX STUDIO", "base_mod": "Original-Mod:", "sub_mod": "Submod:", "browse": "Durchsuchen...", "scan_btn": "⚡ Analyse", "file_label": "GFX-Explorer:", "search_hint": "Suchen...", "all_folders": "Alle Ordner", "clear_btn": "✕", "back_btn": "◀ Zurück", "theme_btn": "Thema", "orig_view": "ORIGINAL", "sub_view": "ERSATZ", "not_found": "NICHT GEFUNDEN", "select_file": "Datei wählen", "start_replace": "▶  START", "success_title": "Erfolg", "success_msg": "Erfolgreich!", "loading": "Laden...", "size_lbl": "Größe: ", "err_dir": "Fehler!", "btn_fit": "Anpassen", "btn_fill": "Füllen", "btn_stretch": "Strecken", "zoom_lbl": "Zoom: ", "img_missing": "BILD FEHLT", "editor_title": "Editor", "editor_save": "✔ Speichern", "editor_preset": "Preset:"},
    "FR": {"title": "HOI4 GFX STUDIO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Parcourir...", "scan_btn": "⚡ Analyser", "file_label": "Explorateur GFX:", "search_hint": "Rechercher...", "all_folders": "Tous les dossiers", "clear_btn": "✕", "back_btn": "◀ Retour", "theme_btn": "Thème", "orig_view": "ORIGINAL", "sub_view": "REMPLACEMENT", "not_found": "NON TROUVÉ", "select_file": "Choisir", "start_replace": "▶  START", "success_title": "Succès", "success_msg": "Réussi !", "loading": "Chargement...", "size_lbl": "Taille: ", "err_dir": "Erreur !", "btn_fit": "Ajuster", "btn_fill": "Remplir", "btn_stretch": "Étirer", "zoom_lbl": "Zoom: ", "img_missing": "IMAGE MANQUANTE", "editor_title": "Éditeur", "editor_save": "✔ Enregistrer", "editor_preset": "Préréglage:"},
    "ES": {"title": "HOI4 GFX STUDIO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Examinar...", "scan_btn": "⚡ Analizar", "file_label": "Explorador GFX:", "search_hint": "Buscar...", "all_folders": "Todas las carpetas", "clear_btn": "✕", "back_btn": "◀ Atrás", "theme_btn": "Tema", "orig_view": "ORIGINAL", "sub_view": "REEMPLAZO", "not_found": "NO ENCONTRADO", "select_file": "Seleccionar", "start_replace": "▶  START", "success_title": "Éxito", "success_msg": "¡Éxito!", "loading": "Cargando...", "size_lbl": "Tamaño: ", "err_dir": "¡Error!", "btn_fit": "Ajustar", "btn_fill": "Llenar", "btn_stretch": "Estirar", "zoom_lbl": "Zoom: ", "img_missing": "IMAGEN FALTA", "editor_title": "Editor", "editor_save": "✔ Guardar", "editor_preset": "Preajuste:"},
    "PT": {"title": "HOI4 GFX STUDIO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Procurar...", "scan_btn": "⚡ Analisar", "file_label": "Explorador GFX:", "search_hint": "Pesquisar...", "all_folders": "Todas as pastas", "clear_btn": "✕", "back_btn": "◀ Voltar", "theme_btn": "Tema", "orig_view": "ORIGINAL", "sub_view": "SUBSTITUIÇÃO", "not_found": "NÃO ENCONTRADO", "select_file": "Selecionar", "start_replace": "▶  START", "success_title": "Sucesso", "success_msg": "Sucesso!", "loading": "Carregando...", "size_lbl": "Tamanho: ", "err_dir": "Erro!", "btn_fit": "Ajustar", "btn_fill": "Preencher", "btn_stretch": "Esticar", "zoom_lbl": "Zoom: ", "img_missing": "IMAGEM FALTA", "editor_title": "Editor", "editor_save": "✔ Salvar", "editor_preset": "Predefinição:"},
    "CN": {"title": "HOI4 GFX STUDIO", "base_mod": "原模组:", "sub_mod": "子模组:", "browse": "浏览...", "scan_btn": "⚡ 分析", "file_label": "GFX 资源管理器:", "search_hint": "搜索...", "all_folders": "所有文件夹", "clear_btn": "✕", "back_btn": "◀ 返回", "theme_btn": "切换主题", "orig_view": "原图", "sub_view": "替换", "not_found": "未找到", "select_file": "选择文件", "start_replace": "▶  开始", "success_title": "成功", "success_msg": "成功！", "loading": "加载中...", "size_lbl": "尺寸: ", "err_dir": "错误！", "btn_fit": "适应", "btn_fill": "填充", "btn_stretch": "拉伸", "zoom_lbl": "缩放: ", "img_missing": "缺少图像", "editor_title": "编辑器", "editor_save": "✔ 保存", "editor_preset": "预设:"}
}

# --- ПРЕСЕТЫ HOI4 ---
HOI4_PRESETS = {
    "Leader Portrait (156x207)": (156, 207),
    "Event Picture (156x225)": (156, 225),
    "National Focus (80x130)": (80, 130),
    "Idea/Minister (60x68)": (60, 68),
    "Custom (Free)": None
}

# --- ЦВЕТОВАЯ ПАЛИТРА SYNTHWAVE ---
NEON_PINK   = "#FF2D78"
NEON_PURPLE = "#9B30FF"
NEON_BLUE   = "#1E90FF"
NEON_CYAN   = "#00F5FF"
DARK_BG     = "#0D0D1A"
PANEL_BG    = "#12122A"
PANEL_DARK  = "#0A0A18"
BORDER_CLR  = "#2A1F5C"
TEXT_MAIN   = "#E8E0FF"
TEXT_DIM    = "#7070A0"
SUCCESS_CLR = "#39FF7A"
FAIL_CLR    = "#FF3860"

# --- ГЛАВНЫЙ STYLESHEET ---
def get_main_stylesheet():
    return f"""
    QMainWindow, QDialog {{
        background-color: {DARK_BG};
    }}
    QWidget {{
        background-color: transparent;
        color: {TEXT_MAIN};
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 10pt;
    }}
    /* ── Панели ── */
    #TopPanel {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {PANEL_BG}, stop:1 {PANEL_DARK});
        border-bottom: 1px solid {BORDER_CLR};
    }}
    #LeftPanel {{
        background: {PANEL_BG};
        border-right: 1px solid {BORDER_CLR};
    }}
    #RightPanel {{
        background: {PANEL_DARK};
    }}    /* ── Поля ввода ── */
    QLineEdit {{
        background-color: #0A0A1E;
        color: {TEXT_MAIN};
        border: 1px solid {BORDER_CLR};
        border-radius: 4px;
        padding: 5px 8px;
        font-family: 'Consolas', monospace;
        selection-background-color: {NEON_PURPLE};
    }}
    QLineEdit:focus {{
        border: 1px solid {NEON_PURPLE};
    }}
    /* ── ComboBox ── */
    QComboBox {{
        background-color: #0A0A1E;
        color: {TEXT_MAIN};
        border: 1px solid {BORDER_CLR};
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: {NEON_PURPLE};
    }}
    QComboBox:hover {{ border-color: {NEON_PURPLE}; }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {PANEL_BG};
        color: {TEXT_MAIN};
        border: 1px solid {NEON_PURPLE};
        selection-background-color: {NEON_PURPLE};
        outline: none;
    }}
    /* ── TreeWidget ── */
    QTreeWidget {{
        background-color: {PANEL_DARK};
        color: {TEXT_MAIN};
        border: 1px solid {BORDER_CLR};
        border-radius: 6px;
        outline: none;
        font-size: 10pt;
    }}
    QTreeWidget::item {{
        padding: 5px 2px;
        border-bottom: 1px solid #1A1A35;
    }}
    QTreeWidget::item:hover {{
        background-color: #1E1E40;
    }}
    QTreeWidget::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {NEON_PURPLE}66, stop:1 {NEON_BLUE}44);
        color: white;
    }}
    QTreeWidget::branch {{
        background-color: {PANEL_DARK};
    }}
    /* ── Scrollbar ── */
    QScrollBar:vertical {{
        background: {PANEL_DARK};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {NEON_PURPLE}88;
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {NEON_PURPLE};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {PANEL_DARK};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {NEON_PURPLE}88;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {NEON_PURPLE};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    /* ── Labels ── */
    QLabel {{
        color: {TEXT_MAIN};
        background: transparent;
    }}
    #NavLabel {{
        color: {NEON_CYAN};
        font-family: 'Consolas', monospace;
        font-size: 9pt;
    }}
    #SectionHeader {{
        color: {NEON_PINK};
        font-size: 11pt;
        font-weight: bold;
    }}
    #FilenameLabel {{
        color: {TEXT_MAIN};
        font-size: 13pt;
        font-weight: bold;
    }}
    #SizeLabel {{
        color: {TEXT_DIM};
        font-size: 9pt;
    }}
    #ViewLabel {{
        color: {TEXT_DIM};
        font-size: 8pt;
        font-weight: bold;
        letter-spacing: 2px;
    }}
    /* ── Кнопка SCAN ── */
    #ScanButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {NEON_PINK}, stop:1 {NEON_PURPLE});
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-size: 11pt;
        font-weight: bold;
    }}
    #ScanButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #FF5599, stop:1 #BB55FF);
    }}
    #ScanButton:pressed {{
        background: {NEON_PURPLE};
    }}
    /* ── Кнопка REPLACE ── */
    #ReplaceButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {NEON_BLUE}, stop:1 {NEON_CYAN});
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 30px;
        font-size: 12pt;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    #ReplaceButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3399FF, stop:1 #33FFFF);
    }}
    #ReplaceButton:pressed {{
        background: {NEON_BLUE};
    }}
    #ReplaceButton:disabled {{
        background: #1A1A3A;
        color: {TEXT_DIM};
    }}
    /* ── Обычные кнопки ── */
    #NavButton {{
        background-color: rgba(26, 26, 53, 120);
        color: {TEXT_DIM};
        border: 1px solid {BORDER_CLR};
        border-radius: 5px;
        padding: 5px 12px;
        font-size: 9pt;
        font-weight: bold;
    }}
    #NavButton:hover {{
        background-color: rgba(37, 37, 80, 160);
        color: {TEXT_MAIN};
        border-color: {NEON_PURPLE};
    }}
    #BrowseButton {{
        background-color: rgba(26, 26, 53, 100);
        color: {NEON_CYAN};
        border: 1px solid {NEON_BLUE}55;
        border-radius: 4px;
        padding: 5px 12px;
        font-size: 9pt;
    }}
    #BrowseButton:hover {{
        background-color: rgba(30, 144, 255, 50);
        border-color: {NEON_CYAN};
    }}
    #ThemeButton {{
        background-color: rgba(26, 26, 53, 100);
        color: {TEXT_DIM};
        border: 1px solid {BORDER_CLR};
        border-radius: 5px;
        padding: 5px 12px;
        font-size: 9pt;
    }}
    #ThemeButton:hover {{
        background-color: rgba(37, 37, 80, 160);
        color: {TEXT_MAIN};
        border-color: {NEON_PURPLE}88;
    }}
    #ClearButton {{
        background-color: rgba(26, 26, 53, 100);
        color: {FAIL_CLR};
        border: 1px solid {BORDER_CLR};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 9pt;
        font-weight: bold;
    }}
    #ClearButton:hover {{
        background-color: rgba(255, 56, 96, 50);
        border-color: {FAIL_CLR};
    }}
    /* ── Canvas label ── */
    #ImageCanvas {{
        background-color: #08081A;
        border: 1px solid {BORDER_CLR};
        border-radius: 8px;
        color: {TEXT_DIM};
    }}
    /* ── ProgressBar ── */
    QProgressBar {{
        background-color: #08081A;
        border: 1px solid {BORDER_CLR};
        border-radius: 4px;
        height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {NEON_PINK}, stop:1 {NEON_PURPLE});
        border-radius: 4px;
    }}
    /* ── Editor buttons ── */
    #EditorBtn {{
        background-color: rgba(26, 26, 53, 100);
        color: {TEXT_MAIN};
        border: 1px solid {BORDER_CLR};
        border-radius: 5px;
        padding: 5px 14px;
        font-size: 9pt;
    }}
    #EditorBtn:hover {{
        background-color: rgba(155, 48, 255, 60);
        border-color: {NEON_PURPLE};
    }}
    #SaveButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {NEON_PINK}, stop:1 {NEON_PURPLE});
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-size: 10pt;
        font-weight: bold;
    }}
    #SaveButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #FF5599, stop:1 #BB55FF);
    }}
    /* ── Tooltip ── */
    QToolTip {{
        background-color: {PANEL_BG};
        color: {TEXT_MAIN};
        border: 1px solid {NEON_PURPLE};
        padding: 4px;
    }}
    """

# ====================== WINDOWS ЭФФЕКТ ======================
def apply_windows_effect(win_id, is_dark=True):
    if platform.system() == "Windows":
        try:
            hwnd = ctypes.windll.user32.GetParent(win_id)
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(ctypes.c_int(2 if is_dark else 0)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(ctypes.c_int(3)), 4)
        except Exception:
            pass

# ====================== НEON LINE WIDGET ======================
class NeonLineWidget(QWidget):
    """Анимированная неон-полоса в цветах UI (синий→фиолетовый→розовый)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self):
        self._phase = (self._phase + 0.012) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        p = self._phase
        c1 = QColor(NEON_BLUE)
        c2 = QColor(NEON_PURPLE)
        c3 = QColor(NEON_PINK)

        grad = QLinearGradient(0, 0, w, 0)
        # FIX: instead of shifting stops (which can collide and cause Qt warnings),
        # shift the colour assignment around the fixed 0/0.33/0.66/1.0 stops.
        colors = [c1, c2, c3, c1]
        offset = int(p * 3) % 3          # 0, 1, or 2 — rotates every 1/3 phase
        rotated = colors[offset:] + colors[:offset]
        stops = [0.0, 0.33, 0.66, 1.0]
        for s, c in zip(stops, rotated):
            grad.setColorAt(s, c)

        painter.fillRect(self.rect(), QBrush(grad))

# ====================== АНИМАЦИОННЫЙ ДВИЖОК ======================

class FadeAnimator:
    """Плавный fade-in/out для любого QWidget через opacity-маску."""
    def __init__(self, widget, duration_ms=350, on_done=None):
        self._w = widget
        self._alpha = 0.0
        self._target = 1.0
        self._step = 1.0 / max(1, duration_ms // 16)
        self._on_done = on_done
        self._timer = QTimer()
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def fade_in(self, on_done=None):
        self._target = 1.0
        self._step = abs(self._step)
        if on_done:
            self._on_done = on_done
        self._timer.start()

    def fade_out(self, on_done=None):
        self._target = 0.0
        self._step = -abs(self._step)
        if on_done:
            self._on_done = on_done
        self._timer.start()

    def _tick(self):
        self._alpha = max(0.0, min(1.0, self._alpha + self._step))
        try:
            effect = self._w.graphicsEffect()
            if effect is None:
                from PyQt6.QtWidgets import QGraphicsOpacityEffect
                effect = QGraphicsOpacityEffect(self._w)
                self._w.setGraphicsEffect(effect)
            effect.setOpacity(self._alpha)
        except Exception:
            pass
        if abs(self._alpha - self._target) < 0.01:
            self._alpha = self._target
            self._timer.stop()
            if self._on_done:
                self._on_done()


class SlideInWidget(QWidget):
    """Враппер: дочерний виджет въезжает снизу/сверху/слева при показе."""
    def __init__(self, child, direction="up", duration_ms=400, parent=None):
        super().__init__(parent)
        self._child = child
        self._dir = direction      # "up" | "down" | "left" | "right"
        self._duration = duration_ms
        self._progress = 0.0      # 0.0 → 1.0
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(child)

    def start(self):
        self._progress = 0.0
        self._timer.start()

    def _ease_out_cubic(self, t):
        return 1 - (1 - t) ** 3

    def _tick(self):
        self._progress = min(1.0, self._progress + 16 / self._duration)
        t = self._ease_out_cubic(self._progress)
        # Animate via temporary transform on child
        offset = int((1.0 - t) * 40)
        if self._dir == "up":
            self._child.move(0, offset)
        elif self._dir == "down":
            self._child.move(0, -offset)
        elif self._dir == "left":
            self._child.move(offset, 0)

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        eff = self._child.graphicsEffect()
        if not isinstance(eff, QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(self._child)
            self._child.setGraphicsEffect(eff)
        eff.setOpacity(t)

        if self._progress >= 1.0:
            self._timer.stop()
            self._child.move(0, 0)
            eff.setOpacity(1.0)


class GlowButton(QPushButton):
    """Кнопка с живым неоновым свечением: ripple при клике, breathing glow когда enabled."""
    def __init__(self, text="", parent=None, glow_color="#9B30FF"):
        super().__init__(text, parent)
        self._glow_color = QColor(glow_color)
        self._glow_alpha = 0
        self._glow_dir = 1
        self._ripple_radius = 0
        self._ripple_opacity = 0.0
        self._ripple_pos = None
        self._breathing = False

        self._breath_timer = QTimer(self)
        self._breath_timer.setInterval(30)
        self._breath_timer.timeout.connect(self._breath_tick)

        self._ripple_timer = QTimer(self)
        self._ripple_timer.setInterval(16)
        self._ripple_timer.timeout.connect(self._ripple_tick)

    def set_breathing(self, active: bool):
        self._breathing = active
        if active:
            self._glow_alpha = 0
            self._glow_dir = 1
            self._breath_timer.start()
        else:
            self._breath_timer.stop()
            self._glow_alpha = 0
            self.update()

    def _breath_tick(self):
        self._glow_alpha += self._glow_dir * 4
        if self._glow_alpha >= 180:
            self._glow_dir = -1
        elif self._glow_alpha <= 0:
            self._glow_dir = 1
        self._glow_alpha = max(0, min(180, self._glow_alpha))
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._ripple_pos = event.pos()
        self._ripple_radius = 0
        self._ripple_opacity = 0.6
        self._ripple_timer.start()

    def _ripple_tick(self):
        self._ripple_radius += 8
        self._ripple_opacity = max(0.0, self._ripple_opacity - 0.04)
        self.update()
        if self._ripple_opacity <= 0:
            self._ripple_timer.stop()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._glow_alpha > 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = QColor(self._glow_color)
            c.setAlpha(self._glow_alpha)
            pen = QPen(c, 2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
            p.end()
        if self._ripple_pos and self._ripple_opacity > 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            c = QColor(255, 255, 255, int(self._ripple_opacity * 120))
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)
            p.end()


class AnimatedCanvas(QLabel):
    """ImageCanvas с fade-in при смене изображения и переливающейся рамкой."""
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.setObjectName("ImageCanvas")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(placeholder_text)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pil_image = None

        # Рамка переливается
        self._border_phase = 0.0
        self._border_timer = QTimer(self)
        self._border_timer.setInterval(33)
        self._border_timer.timeout.connect(self._border_tick)
        self._border_timer.start()

        # Fade-in при загрузке
        self._fade_alpha = 1.0
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(16)
        self._fade_timer.timeout.connect(self._fade_tick)
        self._fade_in_mode = False

    def _border_tick(self):
        self._border_phase = (self._border_phase + 0.018) % 1.0
        self.update()

    def _fade_tick(self):
        if self._fade_in_mode:
            self._fade_alpha = min(1.0, self._fade_alpha + 0.07)
        else:
            self._fade_alpha = max(0.0, self._fade_alpha - 0.1)
        self.update()
        if self._fade_alpha in (0.0, 1.0):
            self._fade_timer.stop()
            if not self._fade_in_mode and self._pending_img is not None:
                self._apply_image(self._pending_img)
                self._pending_img = None

    def set_pil_image(self, pil_img):
        self._pending_img = pil_img
        if pil_img is None:
            self._pil_image = None
            self.setPixmap(QPixmap())
            self._fade_alpha = 1.0
            self._fade_timer.stop()
            return
        # Fade out → swap → fade in
        self._fade_in_mode = False
        self._fade_timer.start()

    def _apply_image(self, pil_img):
        self._pil_image = pil_img
        self._refresh_pixmap()
        self._fade_in_mode = True
        self._fade_alpha = 0.0
        self._fade_timer.start()

    def _refresh_pixmap(self):
        if self._pil_image is None:
            return
        max_w = max(self.width() - 10, 200)
        max_h = max(self.height() - 10, 200)
        img = self._pil_image.copy()
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        self.setPixmap(QPixmap.fromImage(qimg))
        self.setText("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pil_image:
            self._refresh_pixmap()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Opacity overlay for fade
        if self._fade_alpha < 1.0:
            p = QPainter(self)
            alpha = int((1.0 - self._fade_alpha) * 220)
            p.fillRect(self.rect(), QColor(13, 13, 26, alpha))
            p.end()
        # Animated neon border
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ph = self._border_phase
        r = int(155 + 100 * math.sin(ph * math.pi * 2))
        g = int(48  + 40  * math.sin(ph * math.pi * 2 + 2))
        b = int(255)
        a = int(80 + 60 * math.sin(ph * math.pi * 2 + 1))
        pen = QPen(QColor(r, g, b, a), 1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        p.end()


class NeonProgressBar(QProgressBar):
    """Progress bar с бегущей волной неона."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wave_phase = 0.0
        self._wave_timer = QTimer(self)
        self._wave_timer.setInterval(20)
        self._wave_timer.timeout.connect(self._wave_tick)
        self.setTextVisible(False)
        self.setFixedHeight(6)

    def show(self):
        super().show()
        self._wave_phase = 0.0
        self._wave_timer.start()

    def hide(self):
        self._wave_timer.stop()
        super().hide()

    def _wave_tick(self):
        self._wave_phase = (self._wave_phase + 0.06) % 1.0
        self.update()

    def paintEvent(self, event):
        # Background
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(8, 8, 26, 180))

        # Filled portion
        if self.maximum() > 0:
            ratio = self.value() / self.maximum()
            fill_w = int(self.width() * ratio)
            if fill_w > 0:
                grad = QLinearGradient(0, 0, fill_w, 0)
                grad.setColorAt(0.0, QColor(NEON_PINK))
                grad.setColorAt(0.5, QColor(NEON_PURPLE))
                grad.setColorAt(1.0, QColor(NEON_CYAN))
                p.fillRect(0, 0, fill_w, self.height(), QBrush(grad))

                # Wave highlight
                wave_x = int(self._wave_phase * fill_w)
                shine = QLinearGradient(wave_x - 30, 0, wave_x + 30, 0)
                shine.setColorAt(0.0, QColor(255, 255, 255, 0))
                shine.setColorAt(0.5, QColor(255, 255, 255, 90))
                shine.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.fillRect(max(0, wave_x - 30), 0, 60, self.height(), QBrush(shine))
        p.end()


# ====================== ВЫБОР ЯЗЫКА ======================
class LanguageSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_lang = "RU"
        self.setWindowTitle("HOI4 GFX Studio — Select Language")
        self.setFixedSize(480, 700)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        # Прозрачный фон диалога — фон рисует RetroBgWidget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}
            QWidget {{
                background-color: transparent;
                color: {TEXT_MAIN};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            QPushButton#LangBtn {{
                background-color: rgba(18, 8, 40, 160);
                color: {TEXT_MAIN};
                border: 1px solid rgba(155,48,255,80);
                border-radius: 8px;
                font-size: 11pt;
                text-align: left;
                padding: 0px 16px;
            }}
            QPushButton#LangBtn:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155,48,255,90), stop:1 rgba(30,144,255,50));
                border: 1px solid {NEON_PURPLE};
                color: white;
            }}
            QPushButton#LangBtn:pressed {{
                background-color: rgba(155,48,255,130);
                border-color: {NEON_PINK};
            }}
        """)

        # ── Stacked layout: фон + контент ──
        from PyQt6.QtWidgets import QStackedLayout
        stack = QStackedLayout(self)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack.setContentsMargins(0, 0, 0, 0)

        # Слой 0: анимированный retrowave фон
        self._bg = RetroBgWidget(self)
        stack.addWidget(self._bg)

        # Слой 1: контент
        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        stack.addWidget(content)
        stack.setCurrentWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(10)

        # Неон-линия сверху
        layout.addWidget(NeonLineWidget())
        layout.addSpacing(18)

        # Заголовок с неоновым свечением
        title = QLabel("SELECT LANGUAGE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {NEON_CYAN};
            font-size: 22pt;
            font-weight: bold;
            letter-spacing: 4px;
            background: transparent;
        """)
        layout.addWidget(title)

        sub = QLabel("HOI4 GFX Studio")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10pt; background: transparent;")
        layout.addWidget(sub)
        layout.addSpacing(18)

        # Языки с кодом и названием
        langs = [
            ("RU", "РУССКИЙ"),   ("EN", "ENGLISH"),
            ("JA", "日本語"),     ("KO", "한국어"),
            ("DE", "DEUTSCH"),   ("FR", "FRANÇAIS"),
            ("ES", "ESPAÑOL"),   ("PT", "PORTUGUÊS"),
            ("CN", "中文"),
        ]
        self._lang_buttons = []
        for idx, (code, name) in enumerate(langs):
            btn = QPushButton()
            btn.setObjectName("LangBtn")
            btn.setFixedHeight(44)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            btn_lay = QHBoxLayout(btn)
            btn_lay.setContentsMargins(14, 0, 14, 0)
            btn_lay.setSpacing(12)

            lbl_code = QLabel(code)
            lbl_code.setStyleSheet(f"""
                color: {NEON_CYAN};
                font-size: 9pt;
                font-weight: bold;
                font-family: 'Consolas', monospace;
                letter-spacing: 1px;
                background: transparent;
                min-width: 24px;
            """)
            lbl_code.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_name = QLabel(name)
            lbl_name.setStyleSheet(f"""
                color: {TEXT_MAIN};
                font-size: 11pt;
                background: transparent;
            """)

            lbl_arrow = QLabel("›")
            lbl_arrow.setStyleSheet(f"color: rgba(155,48,255,150); font-size: 14pt; background: transparent;")
            lbl_arrow.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            btn_lay.addWidget(lbl_code)
            btn_lay.addWidget(lbl_name, stretch=1)
            btn_lay.addWidget(lbl_arrow)

            btn.clicked.connect(lambda checked, c=code: self._select(c))
            layout.addWidget(btn)

            # Скрываем кнопку, запускаем stagger-появление
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            eff = QGraphicsOpacityEffect(btn)
            eff.setOpacity(0.0)
            btn.setGraphicsEffect(eff)
            self._lang_buttons.append((btn, eff, idx))

        layout.addStretch()
        layout.addWidget(NeonLineWidget())

    def showEvent(self, event):
        super().showEvent(event)
        # Stagger cascade: каждая кнопка появляется с задержкой 60ms
        self._stagger_index = 0
        self._stagger_timer = QTimer(self)
        self._stagger_timer.setInterval(60)
        self._stagger_timer.timeout.connect(self._stagger_step)
        self._stagger_timer.start()

    def _stagger_step(self):
        if self._stagger_index >= len(self._lang_buttons):
            self._stagger_timer.stop()
            return
        btn, eff, idx = self._lang_buttons[self._stagger_index]
        # Запускаем fade-in для этой кнопки
        anim_timer = QTimer(self)
        anim_timer.setInterval(16)
        alpha_holder = [0.0]
        def tick():
            alpha_holder[0] = min(1.0, alpha_holder[0] + 0.1)
            t = alpha_holder[0]
            # ease out cubic
            t_ease = 1 - (1 - t) ** 3
            eff.setOpacity(t_ease)
            if alpha_holder[0] >= 1.0:
                anim_timer.stop()
        anim_timer.timeout.connect(tick)
        anim_timer.start()
        self._stagger_index += 1

    def _select(self, code):
        self.result_lang = code
        self.accept()

    def closeEvent(self, event):
        sys.exit()

# ====================== ФОНОВЫЙ ПОТОК ЗАГРУЗКИ ======================
class ImageLoaderThread(QThread):
    done = pyqtSignal(object, object, str)

    def __init__(self, orig_path, sub_path, max_size=(500, 500)):
        super().__init__()
        self.orig_path = orig_path
        self.sub_path = sub_path
        self.max_size = max_size

    def run(self):
        # FIX: read original size inside _load to avoid opening file twice
        orig_pil, sz = self._load(self.orig_path, return_size=True)
        sub_pil, _ = self._load(self.sub_path)
        self.done.emit(orig_pil, sub_pil, sz)

    def _load(self, path, return_size=False):
        if not path or not os.path.exists(path):
            return (None, "") if return_size else (None, "")
        try:
            with Image.open(path) as img:
                img.load()
                orig_w, orig_h = img.width, img.height
                thumb = img.copy().convert("RGBA")
                thumb.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                sz = f"{orig_w}x{orig_h}" if return_size else ""
                return (thumb, sz)
        except Exception:
            return (None, "") if return_size else (None, "")

# ====================== КАНВАС ДЛЯ ИЗОБРАЖЕНИЯ ======================
# AnimatedCanvas объявлен выше в блоке анимационного движка.
# Оставляем псевдоним для совместимости с остальным кодом.
ImageCanvas = AnimatedCanvas

def pil_to_qpixmap(pil_img):
    if pil_img is None:
        return QPixmap()
    rgba = pil_img.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimg = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)

# ====================== РЕДАКТОР ИЗОБРАЖЕНИЙ ======================
class ImageEditorPro(QDialog):
    def __init__(self, parent, src_img_path, dest_img_path, base_img_path, lang_dict, callback):
        super().__init__(parent)
        self.setWindowTitle(lang_dict.get("editor_title", "Image Editor"))
        self.resize(900, 700)
        self.setStyleSheet(get_main_stylesheet())

        self.src_img_path = src_img_path
        self.dest_img_path = dest_img_path
        self.base_img_path = base_img_path
        self.callback = callback
        self.lang = lang_dict

        self.target_w, self.target_h = self._get_base_dims()
        self.presets = {}
        if self.target_w and self.target_h:
            self.presets["Auto Match Original"] = (self.target_w, self.target_h)
            self.current_preset = "Auto Match Original"
        else:
            self.current_preset = "Leader Portrait (156x207)"
        self.presets.update(HOI4_PRESETS)

        with Image.open(src_img_path) as img:
            self.original_img = img.convert("RGBA")

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._drag_start = None
        self._tk_img_ref = None

        self._build_ui()
        self.do_fill()
        self._update_canvas()

    def _get_base_dims(self):
        try:
            if os.path.exists(self.base_img_path):
                with Image.open(self.base_img_path) as img:
                    return img.width, img.height
        except Exception:
            pass
        return None, None

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top = QFrame()
        top.setObjectName("TopPanel")
        top.setFixedHeight(56)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(12, 6, 12, 6)
        top_layout.setSpacing(8)

        preset_lbl = QLabel(self.lang.get("editor_preset", "Preset:"))
        preset_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt;")
        top_layout.addWidget(preset_lbl)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.presets.keys()))
        self.preset_combo.setCurrentText(self.current_preset)
        self.preset_combo.currentTextChanged.connect(self._on_preset_change)
        self.preset_combo.setFixedWidth(200)
        top_layout.addWidget(self.preset_combo)
        top_layout.addSpacing(10)

        for text, slot in [
            (self.lang.get("btn_fit", "Fit"),     self.do_fit),
            (self.lang.get("btn_fill", "Fill"),   self.do_fill),
            (self.lang.get("btn_stretch", "Stretch"), self.do_stretch),
        ]:
            b = QPushButton(text)
            b.setObjectName("EditorBtn")
            b.clicked.connect(slot)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            top_layout.addWidget(b)

        self.zoom_lbl = QLabel(self.lang.get("zoom_lbl", "Zoom: ") + "100%")
        self.zoom_lbl.setStyleSheet(f"color: {NEON_CYAN}; font-size: 10pt; font-weight: bold;")
        top_layout.addSpacing(10)
        top_layout.addWidget(self.zoom_lbl)
        top_layout.addStretch()

        save_btn = QPushButton(self.lang.get("editor_save", "Apply & Save"))
        save_btn.setObjectName("SaveButton")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self._save_image)
        top_layout.addWidget(save_btn)

        layout.addWidget(top)
        layout.addWidget(NeonLineWidget())

        # Canvas
        self.canvas = QLabel()
        self.canvas.setObjectName("ImageCanvas")
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setStyleSheet(f"background-color: #06060F; border: none;")
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMouseTracking(True)
        layout.addWidget(self.canvas)

        self.canvas.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.canvas:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._drag_start = event.pos()
            elif event.type() == QEvent.Type.MouseMove and self._drag_start:
                dx = event.pos().x() - self._drag_start.x()
                dy = event.pos().y() - self._drag_start.y()
                self.offset_x += dx
                self.offset_y += dy
                self._drag_start = event.pos()
                self._update_canvas()
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_start = None
            elif event.type() == QEvent.Type.Wheel:
                delta = event.angleDelta().y()
                factor = 1.1 if delta > 0 else 0.9
                self.scale_x *= factor
                self.scale_y *= factor
                self._update_canvas()
            elif event.type() == QEvent.Type.Resize:
                self._update_canvas()
        return super().eventFilter(obj, event)

    def _get_target_dims(self):
        s = self.presets.get(self.current_preset)
        return s if s else (self.original_img.width, self.original_img.height)

    def do_fit(self):
        tw, th = self._get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        s = min(tw/w, th/h)
        self.scale_x = self.scale_y = s
        self.offset_x = self.offset_y = 0
        self._update_canvas()

    def do_fill(self):
        tw, th = self._get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        s = max(tw/w, th/h)
        self.scale_x = self.scale_y = s
        self.offset_x = self.offset_y = 0
        self._update_canvas()

    def do_stretch(self):
        tw, th = self._get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        self.scale_x = tw/w
        self.scale_y = th/h
        self.offset_x = self.offset_y = 0
        self._update_canvas()

    def _on_preset_change(self, text):
        self.current_preset = text
        self.do_fill()

    def _update_canvas(self):
        c_w = self.canvas.width()
        c_h = self.canvas.height()
        if c_w <= 1:
            c_w, c_h = 800, 600

        target_size = self.presets.get(self.current_preset)
        if target_size:
            tw, th = target_size
        else:
            tw = int(self.original_img.width * self.scale_x)
            th = int(self.original_img.height * self.scale_y)

        sw = int(self.original_img.width * self.scale_x)
        sh = int(self.original_img.height * self.scale_y)
        if sw <= 0 or sh <= 0: return

        canvas_img = Image.new("RGBA", (c_w, c_h), (6, 6, 15, 255))

        resized = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)
        cx, cy = c_w // 2, c_h // 2

        if target_size:
            img_x = cx - tw // 2 + (tw - sw) // 2 + self.offset_x
            img_y = cy - th // 2 + (th - sh) // 2 + self.offset_y
        else:
            img_x = cx - sw // 2 + self.offset_x
            img_y = cy - sh // 2 + self.offset_y

        # Затемнение за пределами
        if target_size:
            overlay = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 140))
            # FIX: use alpha_composite instead of paste for correct RGBA blending
            canvas_img = Image.alpha_composite(canvas_img, overlay)

        # FIX: PIL paste() raises if coords are entirely outside the canvas;
        # clamp with a crop so partially-offscreen images still render safely
        if img_x < -sw or img_y < -sh or img_x > c_w or img_y > c_h:
            pass  # fully out of bounds — skip paste, nothing visible
        else:
            canvas_img.paste(resized, (img_x, img_y), resized)

        if target_size:
            draw = ImageDraw.Draw(canvas_img)
            rx1 = cx - tw // 2
            ry1 = cy - th // 2
            rx2 = cx + tw // 2
            ry2 = cy + th // 2
            # Рамка цели
            for i in range(2):
                draw.rectangle([rx1-i, ry1-i, rx2+i, ry2+i], outline=(155, 48, 255, 200))

        data = canvas_img.tobytes("raw", "RGBA")
        qimg = QImage(data, c_w, c_h, QImage.Format.Format_RGBA8888)
        self.canvas.setPixmap(QPixmap.fromImage(qimg))

        avg_zoom = int((self.scale_x + self.scale_y) / 2.0 * 100)
        self.zoom_lbl.setText(f"{self.lang.get('zoom_lbl', 'Zoom: ')}{avg_zoom}%")

    def _save_image(self):
        target_size = self.presets.get(self.current_preset)
        if target_size:
            tw, th = target_size
            final_img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            sw = int(self.original_img.width * self.scale_x)
            sh = int(self.original_img.height * self.scale_y)
            resized = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)
            paste_x = (tw - sw) // 2 + self.offset_x
            paste_y = (th - sh) // 2 + self.offset_y
            final_img.paste(resized, (paste_x, paste_y), resized)
        else:
            sw = int(self.original_img.width * self.scale_x)
            sh = int(self.original_img.height * self.scale_y)
            final_img = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)

        dest_dir = os.path.dirname(self.dest_img_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        try:
            ext = os.path.splitext(self.dest_img_path)[1].lower()
            if ext == '.dds':
                # FIX: PIL has no native DDS write support; try imageio first, fallback to PNG copy
                try:
                    import imageio
                    import numpy as np
                    imageio.imwrite(self.dest_img_path, np.array(final_img))
                except Exception:
                    # Last resort: save as PNG with .dds extension (preserves data)
                    final_img.save(self.dest_img_path, format="PNG")
            elif ext == '.tga':
                # Ensure RGBA for TGA with transparency
                final_img.save(self.dest_img_path, format="TGA")
            else:
                final_img.save(self.dest_img_path)
            self.callback()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}")

# ====================== ПРЕВЬЮ ВСПЛЫВАЮЩЕЕ ======================
class HoverPreview(QDialog):
    def __init__(self, parent, pil_img, missing_text):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            #PreviewFrame {{
                background-color: {PANEL_BG};
                border: 1px solid {NEON_PURPLE};
                border-radius: 8px;
            }}
        """)
        frame = QFrame(self)
        frame.setObjectName("PreviewFrame")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(6, 6, 6, 6)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(frame)

        if pil_img:
            lbl = QLabel()
            px = pil_to_qpixmap(pil_img)
            lbl.setPixmap(px)
            lay.addWidget(lbl)
        else:
            lbl = QLabel(missing_text)
            lbl.setStyleSheet(f"color: {FAIL_CLR}; font-size: 11pt; font-weight: bold; padding: 20px;")
            lay.addWidget(lbl)

# ====================== RETROWAVE АНИМИРОВАННЫЙ ФОН ======================
class RetroBgWidget(QWidget):
    """
    Полноэкранный анимированный retrowave фон:
    - тёмное небо с градиентом
    - горы-силуэты
    - анимированная перспективная сетка
    - TV-дрожание (shake) экрана
    - ЭЛТ-помехи (scanlines, noise, glitch) в цветах UI
    - хроматическая аберрация на горизонте
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._rng = random.Random(42)

        self._phase    = 0.0
        self._scanline = 0.0
        self._glitch   = 0.0

        # TV-дрожание
        self._shake_x   = 0
        self._shake_y   = 0
        self._shake_tick = 0

        # Glitch-блоки
        self._noise_lines   = []
        self._glitch_blocks = []
        self._noise_tick    = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        # Таймер запускается в showEvent, а не сразу — не тратим CPU до показа окна

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(33)  # ~30 fps

    def _tick(self):
        self._phase    = (self._phase    + 0.018) % 1.0
        self._scanline = (self._scanline + 0.055) % 1.0
        self._glitch   = (self._glitch   + 0.025) % 1.0

        # ── TV-дрожание ─────────────────────────────────────
        # Лёгкое постоянное дрожание + редкие сильные импульсы
        self._shake_tick += 1
        base_shake = 1
        if self._shake_tick % 120 < 6:          # сильный импульс раз в ~4 сек
            base_shake = random.randint(3, 7)
        elif self._shake_tick % 30 < 4:          # средний каждую секунду
            base_shake = random.randint(1, 3)
        self._shake_x = random.randint(-base_shake, base_shake)
        self._shake_y = random.randint(-base_shake, base_shake)

        # ── Кэш noise-линий + glitch-блоков ─────────────────
        self._noise_tick += 1
        if self._noise_tick >= 3:   # обновляем каждые 3 кадра (≈10 fps — быстрее)
            self._noise_tick = 0
            rng = random.Random(int(self._glitch * 99991))
            neon = [
                (155, 48, 255), (30, 144, 255),
                (255, 45, 120), (0, 245, 255),
                (255, 45, 120), (155, 48, 255),   # розовый и пурпур чаще
            ]
            # Горизонтальные glitch-штрихи (больше и ярче)
            self._noise_lines = []
            n = 28 if (self._shake_tick % 90 < 8) else 18
            for _ in range(n):
                y   = rng.randint(0, 1000)
                x   = rng.randint(0, 800)
                ln  = rng.randint(15, 260)
                col = neon[rng.randint(0, len(neon)-1)]
                a   = rng.randint(25, 90)
                thick = rng.randint(1, 2)
                self._noise_lines.append((y, x, ln, col, a, thick))

            # Прямоугольные glitch-блоки (полупрозрачные)
            self._glitch_blocks = []
            if rng.random() < 0.35:   # 35% шанс каждые 3 кадра
                for _ in range(rng.randint(1, 4)):
                    gy  = rng.randint(0, 1000)
                    gh  = rng.randint(2, 12)
                    gx  = rng.randint(0, 700)
                    gw  = rng.randint(40, 300)
                    col = neon[rng.randint(0, len(neon)-1)]
                    a   = rng.randint(12, 40)
                    self._glitch_blocks.append((gy, gh, gx, gw, col, a))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        # ── TV-дрожание: сдвигаем весь painter ───────────────
        if self._shake_x or self._shake_y:
            p.translate(self._shake_x, self._shake_y)

        horizon = int(h * 0.52)

        # ── 1. SKY GRADIENT ──────────────────────────────────
        sky = QLinearGradient(0, 0, 0, horizon)
        sky.setColorAt(0.0,  QColor(8,  5,  28))
        sky.setColorAt(0.45, QColor(28, 8,  55))
        sky.setColorAt(0.75, QColor(70, 10, 80))
        sky.setColorAt(1.0,  QColor(120, 20, 90))
        p.fillRect(0, 0, w, horizon, QBrush(sky))

        # ── 2. ЗЕМЛЯ ─────────────────────────────────────────
        ground = QLinearGradient(0, horizon, 0, h)
        ground.setColorAt(0.0, QColor(15, 5, 30))
        ground.setColorAt(1.0, QColor(5,  2, 15))
        p.fillRect(0, horizon, w, h - horizon, QBrush(ground))

        # ── 3. СОЛНЦЕ — клипировано горизонтом ───────────────
        sun_cx = w // 2
        sun_cy = int(horizon * 0.68)
        sun_r  = int(min(w, h) * 0.18)

        p.save()
        p.setClipRect(0, 0, w, horizon)

        sun_grad = QRadialGradient(sun_cx, sun_cy, sun_r)
        sun_grad.setColorAt(0.0, QColor(255, 140, 190))
        sun_grad.setColorAt(0.5, QColor(220, 60,  160))
        sun_grad.setColorAt(1.0, QColor(140, 20,  120))
        p.setBrush(QBrush(sun_grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(sun_cx - sun_r, sun_cy - sun_r, sun_r * 2, sun_r * 2)

        # Горизонтальные полосы внутри солнца
        n_stripes = 7
        stripe_top = sun_cy + int(sun_r * 0.05)
        stripe_bot = sun_cy + sun_r
        zone_h = stripe_bot - stripe_top
        for i in range(n_stripes):
            t  = i / n_stripes
            sy = stripe_top + int(zone_h * t)
            sh = max(2, int(zone_h / (n_stripes * 1.6)))
            dy = sy - sun_cy
            if abs(dy) < sun_r:
                half_w = int(math.sqrt(max(0, sun_r**2 - dy**2)))
                p.fillRect(sun_cx - half_w, sy, half_w * 2, sh, QColor(20, 10, 50, 210))

        # Ободок солнца
        p.setPen(QPen(QColor(255, 80, 200, 120), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(sun_cx - sun_r, sun_cy - sun_r, sun_r * 2, sun_r * 2)
        p.restore()

        # ── 4. ХРОМАТИЧЕСКАЯ АБЕРРАЦИЯ на горизонте ──────────
        # Три смещённых полупрозрачных линии — красный, зелёный, синий канал
        for offset, col in [(-2, QColor(255,45,120,60)), (0, QColor(155,48,255,90)), (2, QColor(0,245,255,60))]:
            p.setPen(QPen(col, 1.5))
            p.drawLine(0, horizon + offset, w, horizon + offset)

        # ── 5. ГОРЫ-СИЛУЭТЫ ───────────────────────────────────
        def mountain_range(pts_def, color):
            pts = [QPoint(int(x * w), int(y * horizon)) for x, y in pts_def]
            pts += [QPoint(w, horizon), QPoint(0, horizon)]
            poly = QPolygon(pts)
            p.setBrush(QBrush(QColor(*color)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(poly)

        mountain_range([
            (0.0,1.0),(0.06,0.55),(0.13,0.72),(0.20,0.40),(0.28,0.62),
            (0.36,0.30),(0.44,0.55),(0.52,0.38),(0.60,0.58),(0.68,0.32),
            (0.76,0.52),(0.84,0.42),(0.92,0.60),(1.0,1.0)
        ], (22, 8, 45, 255))
        mountain_range([
            (0.0,1.0),(0.08,0.75),(0.16,0.85),(0.24,0.60),(0.33,0.80),
            (0.42,0.55),(0.50,0.75),(0.58,0.60),(0.66,0.80),(0.75,0.65),
            (0.83,0.78),(0.91,0.68),(1.0,1.0)
        ], (14, 5, 30, 255))

        # ── 6. ПЕРСПЕКТИВНАЯ СЕТКА ────────────────────────────
        vp_x = w // 2
        vp_y = horizon

        n_h_lines = 14
        for i in range(n_h_lines):
            t = ((i + self._phase) / n_h_lines) ** 1.8
            y = int(horizon + (h - horizon) * t)
            if y > h: continue
            alpha = int(40 + 150 * t)
            p.setPen(QPen(QColor(200, 40, 255, min(alpha, 200)), 1 if t < 0.5 else 1.5))
            p.drawLine(0, y, w, y)

        n_v_lines = 16
        half = n_v_lines // 2
        for i in range(-half, half + 1):
            spread = w * 0.55
            bx = int(vp_x + i * (spread / half))
            alpha = int(90 - abs(i) * 3)
            if alpha < 15: continue
            p.setPen(QPen(QColor(200, 40, 255, max(15, alpha)), 1))
            p.drawLine(vp_x, vp_y, bx, h)

        # ── 7. НИЖНЕЕ СВЕЧЕНИЕ ────────────────────────────────
        glow = QLinearGradient(0, h - int(h * 0.12), 0, h)
        glow.setColorAt(0.0, QColor(180, 30, 220, 0))
        glow.setColorAt(0.6, QColor(200, 40, 255, 60))
        glow.setColorAt(1.0, QColor(220, 60, 255, 120))
        p.fillRect(0, h - int(h * 0.12), w, int(h * 0.12), QBrush(glow))

        # ── 8. CRT SCANLINES — анимированные ─────────────────
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        scan_alpha = int(22 + 12 * math.sin(self._scanline * math.pi * 2))
        scan_offset = int(self._scanline * 4) % 4   # плавное скольжение строк
        for y in range(-scan_offset, h + 4, 4):
            p.fillRect(0, y, w, 2, QColor(0, 0, 0, scan_alpha))

        # ── 9. БЕГУЩАЯ СВЕТЛАЯ СКАН-ЛИНИЯ ────────────────────
        scan_y = int((self._scanline % 1.0) * (h + 60)) - 30
        beam_grad = QLinearGradient(0, scan_y - 3, 0, scan_y + 3)
        beam_grad.setColorAt(0.0, QColor(155, 48, 255, 0))
        beam_grad.setColorAt(0.5, QColor(155, 48, 255, 35))
        beam_grad.setColorAt(1.0, QColor(155, 48, 255, 0))
        p.fillRect(0, max(0, scan_y - 3), w, 6, QBrush(beam_grad))

        # ── 10. GLITCH-БЛОКИ (прямоугольные помехи) ──────────
        for (gy, gh, gx, gw, col, a) in self._glitch_blocks:
            ry = int(gy / 1000 * h)
            rh = int(gh / 1000 * h) + 2
            rx = int(gx / 700  * w)
            rw = int(gw / 700  * w)
            p.fillRect(rx, ry, rw, rh, QColor(col[0], col[1], col[2], a))

        # ── 11. ГОРИЗОНТАЛЬНЫЕ GLITCH-ШТРИХИ ─────────────────
        for (ny, nx, ln, col, a, thick) in self._noise_lines:
            ry  = int(ny / 1000 * h)
            rx  = int(nx / 800  * w)
            rln = int(ln / 800  * w)
            p.setPen(QPen(QColor(col[0], col[1], col[2], a), thick))
            p.drawLine(rx, ry, min(rx + rln, w), ry)

        # ── 12. ВИНЬЕТКА по краям ─────────────────────────────
        vign_l = QLinearGradient(0, 0, int(w * 0.18), 0)
        vign_l.setColorAt(0.0, QColor(0, 0, 0, 80))
        vign_l.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, int(w * 0.18), h, QBrush(vign_l))
        vign_r = QLinearGradient(int(w * 0.82), 0, w, 0)
        vign_r.setColorAt(0.0, QColor(0, 0, 0, 0))
        vign_r.setColorAt(1.0, QColor(0, 0, 0, 80))
        p.fillRect(int(w * 0.82), 0, int(w * 0.18), h, QBrush(vign_r))

        p.end()


# ====================== RETROWAVE ИКОНКИ ======================
_ICON_CACHE: dict = {}

def _make_retro_folder_icon(size: int = 20) -> "QIcon":
    """Нарисованная неоновая иконка папки в стиле Retrowave."""
    from PyQt6.QtGui import QIcon
    key = ("folder", size)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    # --- тело папки (нижняя часть) ---
    body_top  = int(s * 0.32)
    body_left = 0
    body_w    = s - 1
    body_h    = int(s * 0.58)
    body_r    = int(s * 0.12)

    # Заливка тела — тёмная с пурпурным оттенком
    body_fill = QLinearGradient(body_left, body_top, body_left, body_top + body_h)
    body_fill.setColorAt(0.0, QColor(40, 10, 70, 230))
    body_fill.setColorAt(1.0, QColor(20, 5,  40, 230))
    p.setBrush(QBrush(body_fill))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(body_left, body_top, body_w, body_h, body_r, body_r)

    # --- язычок папки (вкладка) ---
    tab_w = int(s * 0.42)
    tab_h = int(s * 0.14)
    tab_r = int(s * 0.08)
    tab_fill = QLinearGradient(0, 0, tab_w, 0)
    tab_fill.setColorAt(0.0, QColor(155, 48, 255, 200))
    tab_fill.setColorAt(1.0, QColor(255, 45, 120, 180))
    p.setBrush(QBrush(tab_fill))
    p.drawRoundedRect(int(s * 0.04), int(s * 0.18), tab_w, tab_h + body_r, tab_r, tab_r)

    # --- неоновые обводки ---
    # Внешнее свечение (широкое, полупрозрачное)
    glow_pen = QPen(QColor(155, 48, 255, 55), 3.5)
    glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(glow_pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(body_left, body_top, body_w, body_h, body_r, body_r)

    # Основная обводка (тонкая, яркая)
    main_pen = QPen(QColor(200, 80, 255, 220), 1.1)
    main_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(main_pen)
    p.drawRoundedRect(body_left, body_top, body_w, body_h, body_r, body_r)

    # Обводка язычка
    tab_pen = QPen(QColor(255, 45, 120, 200), 1.0)
    p.setPen(tab_pen)
    p.drawRoundedRect(int(s * 0.04), int(s * 0.18), tab_w, tab_h + body_r, tab_r, tab_r)

    # --- мини-линии сетки внутри (retrowave grid) ---
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    grid_pen = QPen(QColor(155, 48, 255, 45), 1)
    p.setPen(grid_pen)
    inner_top  = body_top + int(s * 0.12)
    inner_bot  = body_top + body_h - int(s * 0.06)
    inner_left = int(s * 0.10)
    inner_right = body_w - int(s * 0.08)
    # 2 горизонтальные линии
    step = (inner_bot - inner_top) // 3
    for i in range(1, 3):
        y = inner_top + i * step
        p.drawLine(inner_left, y, inner_right, y)
    # блик сверху (светлая полоса)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    shine = QLinearGradient(body_left, body_top, body_left + body_w, body_top)
    shine.setColorAt(0.0, QColor(255, 255, 255, 0))
    shine.setColorAt(0.35, QColor(255, 180, 255, 30))
    shine.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(shine))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(body_left, body_top, body_w, int(body_h * 0.35), body_r, body_r)

    p.end()
    icon = QIcon(QPixmap.fromImage(img))
    _ICON_CACHE[key] = icon
    return icon


def _make_retro_file_icon(size: int = 20, color: str = "cyan") -> "QIcon":
    """Нарисованная неоновая иконка файла (cyan для найденных, red для отсутствующих)."""
    from PyQt6.QtGui import QIcon
    key = ("file", size, color)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    if color == "cyan":
        neon_c  = QColor(0, 245, 255, 220)
        neon_g  = QColor(0, 200, 255, 80)
        fill_c  = QColor(0, 30, 50, 210)
        fill_c2 = QColor(0, 15, 30, 210)
    else:  # red / fail
        neon_c  = QColor(255, 56, 96, 220)
        neon_g  = QColor(255, 56, 96, 70)
        fill_c  = QColor(50, 5, 15, 210)
        fill_c2 = QColor(30, 3, 10, 210)

    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    margin_x = int(s * 0.15)
    margin_y = int(s * 0.06)
    doc_w = s - margin_x * 2
    doc_h = s - margin_y * 2
    corner = int(s * 0.22)   # загнутый угол
    cr = int(s * 0.08)       # радиус скругления

    # Форма документа с загнутым правым верхним углом
    path = QPainterPath()
    path.moveTo(margin_x + cr, margin_y)
    path.lineTo(margin_x + doc_w - corner, margin_y)
    path.lineTo(margin_x + doc_w, margin_y + corner)
    path.lineTo(margin_x + doc_w, margin_y + doc_h - cr)
    path.quadTo(margin_x + doc_w, margin_y + doc_h, margin_x + doc_w - cr, margin_y + doc_h)
    path.lineTo(margin_x + cr, margin_y + doc_h)
    path.quadTo(margin_x, margin_y + doc_h, margin_x, margin_y + doc_h - cr)
    path.lineTo(margin_x, margin_y + cr)
    path.quadTo(margin_x, margin_y, margin_x + cr, margin_y)
    path.closeSubpath()

    # Заливка
    body_fill = QLinearGradient(margin_x, margin_y, margin_x, margin_y + doc_h)
    body_fill.setColorAt(0.0, fill_c)
    body_fill.setColorAt(1.0, fill_c2)
    p.setBrush(QBrush(body_fill))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPath(path)

    # Загнутый уголок
    fold = QPainterPath()
    fold.moveTo(margin_x + doc_w - corner, margin_y)
    fold.lineTo(margin_x + doc_w - corner, margin_y + corner)
    fold.lineTo(margin_x + doc_w, margin_y + corner)
    p.setBrush(QBrush(QColor(neon_c.red(), neon_c.green(), neon_c.blue(), 35)))
    p.drawPath(fold)

    # Линия загнутого уголка
    p.setPen(QPen(neon_c.darker(110), 0.8))
    p.drawLine(int(margin_x + doc_w - corner), margin_y,
               int(margin_x + doc_w - corner), int(margin_y + corner))
    p.drawLine(int(margin_x + doc_w - corner), int(margin_y + corner),
               int(margin_x + doc_w), int(margin_y + corner))

    # Свечение (glow)
    glow_pen = QPen(neon_g, 3.0)
    p.setPen(glow_pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)

    # Основная обводка
    p.setPen(QPen(neon_c, 1.0))
    p.drawPath(path)

    # Строчки текста внутри
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    line_col = QColor(neon_c.red(), neon_c.green(), neon_c.blue(), 70)
    p.setPen(QPen(line_col, 1))
    line_x1 = margin_x + int(s * 0.12)
    line_x2 = margin_x + doc_w - int(s * 0.12)
    line_start_y = margin_y + corner + int(s * 0.06)
    for i in range(3):
        ly = line_start_y + i * int(s * 0.16)
        if ly + 1 < margin_y + doc_h - int(s * 0.06):
            end_x = line_x2 if i < 2 else int(line_x1 + (line_x2 - line_x1) * 0.65)
            p.drawLine(line_x1, ly, end_x, ly)

    p.end()
    icon = QIcon(QPixmap.fromImage(img))
    _ICON_CACHE[key] = icon
    return icon


# ====================== ГЛАВНЫЙ КЛАСС ======================
class HOI4ModdingStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_cache = {}
        self.current_lang = "RU"
        self.current_theme = "dark"
        self._load_config()

        self.files_data = []
        self.last_scanned_dirs = []
        self.current_nav_path = "gfx"
        self.current_selected_rel_path = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._populate_tree)

        self._loader_thread = None
        self._wave_timer = QTimer(self)
        self._wave_timer.timeout.connect(self._tick_wave)
        self._wave_progress = 0
        self._wave_tick = 0.0

        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._show_hover_preview)
        self._hover_preview = None
        self._hovered_item = None
        self._last_hover_pos = QPoint()

        self.setWindowTitle(LANG[self.current_lang]["title"])
        self.resize(1280, 720)
        self._center_window()
        self.setStyleSheet(get_main_stylesheet())

        self._build_ui()
        apply_windows_effect(int(self.winId()), True)
        # Всегда применяем Retrowave
        self._apply_theme()

    def _center_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def _load_config(self):
        self.current_theme = "retrowave"   # всегда Retrowave
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("language") in LANG:
                        self.current_lang = data["language"]
                    return
            except Exception:
                pass
        dlg = LanguageSelector()
        dlg.exec()
        self.current_lang = dlg.result_lang
        self._save_config()

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"language": self.current_lang, "theme": self.current_theme}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── UI ──────────────────────────────────────────────────
    def _build_ui(self):
        from PyQt6.QtWidgets import QStackedLayout

        central = QWidget()
        self.setCentralWidget(central)
        self._central = central

        # QStackedLayout: все дочерние виджеты занимают одно и то же место и растягиваются
        stack = QStackedLayout(central)
        stack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stack.setContentsMargins(0, 0, 0, 0)

        # ── Слой 0: Retrowave анимированный фон ──
        self._retro_bg = RetroBgWidget()
        self._retro_bg.hide()
        stack.addWidget(self._retro_bg)

        # ── Слой 1: основной контент ──
        self._content = QWidget()
        self._content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        stack.addWidget(self._content)
        stack.setCurrentWidget(self._content)   # контент поверх фона

        root_lay = QVBoxLayout(self._content)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Неон линия сверху
        self.neon_line = NeonLineWidget()
        root_lay.addWidget(self.neon_line)

        # TOP PANEL
        top_panel = QFrame()
        top_panel.setObjectName("TopPanel")
        top_panel.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        top_panel.setFixedHeight(80)
        top_lay = QHBoxLayout(top_panel)
        top_lay.setContentsMargins(16, 10, 16, 10)
        top_lay.setSpacing(10)

        # Paths grid
        paths_widget = QWidget()
        paths_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        paths_grid = QVBoxLayout(paths_widget)
        paths_grid.setContentsMargins(0, 0, 0, 0)
        paths_grid.setSpacing(4)

        for attr, key in [("base_path_edit", "base_mod"), ("sub_path_edit", "sub_mod")]:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(LANG[self.current_lang][key])
            lbl.setFixedWidth(160)
            lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt; font-weight: bold;")
            setattr(self, f"lbl_{'base' if attr.startswith('base') else 'sub'}", lbl)
            row.addWidget(lbl)

            edit = QLineEdit()
            edit.setFixedHeight(26)
            setattr(self, attr, edit)
            row.addWidget(edit)

            btn = QPushButton(LANG[self.current_lang]["browse"])
            btn.setObjectName("BrowseButton")
            btn.setFixedWidth(80)
            btn.setFixedHeight(26)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            target_edit = edit
            btn.clicked.connect(lambda checked, e=target_edit: self._get_path(e))
            row.addWidget(btn)
            paths_grid.addLayout(row)

        top_lay.addWidget(paths_widget, stretch=1)

        # Right controls
        right_ctrl = QVBoxLayout()
        right_ctrl.setSpacing(4)

        top_right = QHBoxLayout()
        top_right.setSpacing(6)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(list(LANG.keys()))
        self.lang_combo.setCurrentText(self.current_lang)
        self.lang_combo.setFixedWidth(75)
        self.lang_combo.currentTextChanged.connect(self._change_lang)
        top_right.addWidget(self.lang_combo)

        right_ctrl.addLayout(top_right)

        self.btn_scan = GlowButton(LANG[self.current_lang]["scan_btn"], glow_color=NEON_PINK)
        self.btn_scan.setObjectName("ScanButton")
        self.btn_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scan.clicked.connect(self._scan_files)
        self.btn_scan.setFixedHeight(36)
        right_ctrl.addWidget(self.btn_scan)

        top_lay.addLayout(right_ctrl)
        root_lay.addWidget(top_panel)

        # MAIN SPLITTER
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {BORDER_CLR}; }}")
        # Чтобы фон просвечивал сквозь splitter в режиме retrowave
        self._splitter.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        root_lay.addWidget(self._splitter, stretch=1)

        # ── LEFT PANEL ──
        left_panel = QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(12, 12, 12, 12)
        left_lay.setSpacing(6)

        hdr = QLabel(LANG[self.current_lang]["file_label"])
        hdr.setObjectName("SectionHeader")
        self.lbl_list = hdr
        left_lay.addWidget(hdr)

        self.lbl_nav = QLabel("gfx")
        self.lbl_nav.setObjectName("NavLabel")
        left_lay.addWidget(self.lbl_nav)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(5)

        self.btn_back = QPushButton(LANG[self.current_lang]["back_btn"])
        self.btn_back.setObjectName("NavButton")
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.clicked.connect(self._go_back)
        search_row.addWidget(self.btn_back)

        self.folder_combo = QComboBox()
        self.folder_combo.setFixedWidth(130)
        self.folder_combo.currentTextChanged.connect(self._on_combo_select)
        search_row.addWidget(self.folder_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(LANG[self.current_lang]["search_hint"])
        self.search_edit.textChanged.connect(self._schedule_search)
        search_row.addWidget(self.search_edit, stretch=1)

        self.btn_clear = QPushButton(LANG[self.current_lang]["clear_btn"])
        self.btn_clear.setObjectName("ClearButton")
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.clicked.connect(self._clear_search)
        search_row.addWidget(self.btn_clear)

        left_lay.addLayout(search_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(2)
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(0, False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_select_file)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setMouseTracking(True)
        self.tree.viewport().installEventFilter(self)
        self.tree.viewport().setMouseTracking(True)
        left_lay.addWidget(self.tree, stretch=1)

        self._splitter.addWidget(left_panel)

        # ── RIGHT PANEL ──
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(16, 16, 16, 16)
        right_lay.setSpacing(10)

        self.lbl_filename = QLabel(LANG[self.current_lang]["select_file"])
        self.lbl_filename.setObjectName("FilenameLabel")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_lay.addWidget(self.lbl_filename)

        # Wave progress bar (NeonProgressBar с бегущей волной)
        self.progress_bar = NeonProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        right_lay.addWidget(self.progress_bar)

        # Image viewer
        viewer_row = QHBoxLayout()
        viewer_row.setSpacing(10)

        def make_img_col(view_label_text):
            col = QVBoxLayout()
            lbl_top = QLabel(view_label_text)
            lbl_top.setObjectName("ViewLabel")
            lbl_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl_top)
            canvas = ImageCanvas("")
            col.addWidget(canvas, stretch=1)
            return col, canvas

        left_col, self.orig_canvas = make_img_col(LANG[self.current_lang]["orig_view"])
        right_col2, self.sub_canvas = make_img_col(LANG[self.current_lang]["sub_view"])
        self.lbl_orig_view = left_col.itemAt(0).widget()
        self.lbl_sub_view = right_col2.itemAt(0).widget()

        viewer_row.addLayout(left_col)
        viewer_row.addSpacing(8)
        viewer_row.addLayout(right_col2)
        right_lay.addLayout(viewer_row, stretch=1)

        self.lbl_size = QLabel("")
        self.lbl_size.setObjectName("SizeLabel")
        self.lbl_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_lay.addWidget(self.lbl_size)

        # Replace button — GlowButton с breathing glow
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 0, 20, 0)
        self.btn_replace = GlowButton(LANG[self.current_lang]["start_replace"], glow_color=NEON_CYAN)
        self.btn_replace.setObjectName("ReplaceButton")
        self.btn_replace.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_replace.setEnabled(False)
        self.btn_replace.setFixedHeight(50)
        self.btn_replace.clicked.connect(self._open_image_editor)
        btn_row.addWidget(self.btn_replace)
        right_lay.addLayout(btn_row)

        self._splitter.addWidget(right_panel)
        self._splitter.setSizes([440, 840])

    # ── Hover preview ───────────────────────────────────────
    def eventFilter(self, obj, event):
        if obj == self.tree.viewport():
            if event.type() == QEvent.Type.MouseMove:
                item = self.tree.itemAt(event.pos())
                if item:
                    if self._hovered_item is not item:
                        self._cancel_hover()
                        self._hovered_item = item
                        self._last_hover_pos = event.globalPosition().toPoint()
                        self._hover_timer.start(600)
                else:
                    self._cancel_hover()
            elif event.type() == QEvent.Type.Leave:
                self._cancel_hover()
            elif event.type() == QEvent.Type.MouseButtonPress:
                self._cancel_hover()
        return super().eventFilter(obj, event)

    def _cancel_hover(self, *_):
        self._hover_timer.stop()
        if self._hover_preview:
            self._hover_preview.close()
            self._hover_preview = None
        self._hovered_item = None

    def _show_hover_preview(self):
        if not self._hovered_item:
            return
        f_path = self._hovered_item.data(0, Qt.ItemDataRole.UserRole)
        if not f_path:
            return
        full_path = os.path.join(self.sub_path_edit.text(), f_path)
        pil_img = None
        try:
            if os.path.exists(full_path):
                with Image.open(full_path) as img:
                    img.load()
                    pil_img = img.copy().convert("RGBA")
                    pil_img.thumbnail((260, 260), Image.Resampling.LANCZOS)
        except Exception:
            pil_img = None

        l = LANG.get(self.current_lang, LANG["EN"])
        self._hover_preview = HoverPreview(self, pil_img, l.get("img_missing", "IMAGE MISSING"))
        self._hover_preview.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        pos = self._last_hover_pos + QPoint(15, 15)
        self._hover_preview.move(pos)
        self._hover_preview.show()

    # ── Navigation ──────────────────────────────────────────
    def _get_path(self, edit):
        p = QFileDialog.getExistingDirectory(self, "Select Directory")
        if p:
            edit.setText(os.path.normpath(p))

    def _scan_files(self):
        b_root = self.base_path_edit.text().strip()
        if not b_root or not os.path.exists(os.path.join(b_root, "gfx")):
            QMessageBox.critical(self, "Error", LANG[self.current_lang]["err_dir"])
            return
        # Анимация кнопки сканирования
        self.btn_scan.set_breathing(True)
        self.btn_scan.setEnabled(False)
        self.files_data = []

        def fast_walk(path):
            try:
                for entry in os.scandir(path):
                    if entry.is_dir():
                        yield from fast_walk(entry.path)
                    elif entry.name.lower().endswith(('.dds', '.tga', '.png', '.jpg')):
                        yield os.path.relpath(entry.path, b_root)
            except PermissionError:
                pass

        self.files_data = sorted(list(fast_walk(os.path.join(b_root, "gfx"))))
        top_dirs = set()
        for f in self.files_data:
            parts = f.split(os.sep)
            if len(parts) > 1:
                top_dirs.add(parts[0])
        self.last_scanned_dirs = sorted(list(top_dirs))
        self._sync_nav_ui()
        self._populate_tree()
        # Останавливаем анимацию после завершения
        self.btn_scan.set_breathing(False)
        self.btn_scan.setEnabled(True)

    def _schedule_search(self):
        self._search_timer.start(250)

    def _clear_search(self):
        self.search_edit.setText("")
        self.current_nav_path = "gfx"
        self._sync_nav_ui()
        self._populate_tree()

    def _go_back(self):
        if os.sep in self.current_nav_path:
            self.current_nav_path = os.path.dirname(self.current_nav_path)
            self._sync_nav_ui()
            self._populate_tree()

    def _on_combo_select(self, val):
        l = LANG.get(self.current_lang, LANG["EN"])
        if val == l.get("all_folders", ""):
            self.current_nav_path = "gfx"
        elif val:
            self.current_nav_path = val
        self._populate_tree()

    def _sync_nav_ui(self):
        l = LANG.get(self.current_lang, LANG["EN"])
        all_opt = l["all_folders"]
        options = [all_opt] + self.last_scanned_dirs
        # Block signals to avoid recursive _on_combo_select
        self.folder_combo.blockSignals(True)
        self.folder_combo.clear()
        self.folder_combo.addItems(options)
        if self.current_nav_path == "gfx":
            self.folder_combo.setCurrentText(all_opt)
        else:
            self.folder_combo.setCurrentText(self.current_nav_path)
        self.folder_combo.blockSignals(False)
        nav_text = self.current_nav_path.replace(os.sep, " › ")
        self.lbl_nav.setText(nav_text)

    def _populate_tree(self):
        self.tree.clear()
        search = self.search_edit.text().lower()
        s_root = self.sub_path_edit.text()
        active_path_prefix = self.current_nav_path

        if search:
            nodes = {}
            for f_path in self.files_data:
                if search in f_path.lower() and f_path.startswith(active_path_prefix):
                    parts = f_path.split(os.sep)
                    curr = ""
                    for i, p in enumerate(parts):
                        parent_key = curr
                        curr = os.path.join(curr, p) if curr else p
                        if curr not in nodes:
                            is_file = (i == len(parts) - 1)
                            if parent_key in nodes:
                                parent_item = nodes[parent_key]
                            else:
                                parent_item = self.tree.invisibleRootItem()
                            item = QTreeWidgetItem(parent_item, [p])
                            item.setExpanded(True)
                            if is_file:
                                item.setData(0, Qt.ItemDataRole.UserRole, f_path)
                                exists = os.path.exists(os.path.join(s_root, f_path))
                                item.setForeground(0, QColor(SUCCESS_CLR if exists else FAIL_CLR))
                                item.setIcon(0, _make_retro_file_icon(18, "cyan" if exists else "red"))
                            else:
                                item.setForeground(0, QColor(TEXT_MAIN))
                                item.setIcon(0, _make_retro_folder_icon(18))
                            nodes[curr] = item
        else:
            seen_folders = set()
            for f_path in self.files_data:
                if f_path.startswith(active_path_prefix + os.sep) or f_path == active_path_prefix:
                    rel = os.path.relpath(f_path, active_path_prefix)
                    if rel == ".":
                        continue
                    parts = rel.split(os.sep)
                    name = parts[0]
                    if len(parts) > 1:
                        if name not in seen_folders:
                            full_folder = os.path.join(active_path_prefix, name)
                            item = QTreeWidgetItem(self.tree, [name])
                            item.setIcon(0, _make_retro_folder_icon(18))
                            item.setForeground(0, QColor(NEON_PURPLE))
                            item.setData(0, Qt.ItemDataRole.UserRole + 1, full_folder)
                            seen_folders.add(name)
                    else:
                        exists = os.path.exists(os.path.join(s_root, f_path))
                        item = QTreeWidgetItem(self.tree, [name])
                        item.setIcon(0, _make_retro_file_icon(18, "cyan" if exists else "red"))
                        item.setData(0, Qt.ItemDataRole.UserRole, f_path)
                        item.setForeground(0, QColor(SUCCESS_CLR if exists else FAIL_CLR))

        # Stagger: постепенно показываем элементы через opacity делегат
        self._animate_tree_items()

    def _animate_tree_items(self):
        """Stagger-fade для элементов дерева — каждый появляется с задержкой."""
        root = self.tree.invisibleRootItem()
        count = root.childCount()
        if count == 0:
            return
        # Ограничиваем до 40 элементов для производительности
        limit = min(count, 40)
        self._tree_stagger_idx = 0
        self._tree_stagger_limit = limit
        # Сначала делаем все элементы полупрозрачными через foreground alpha
        # (QTreeWidgetItem не поддерживает opacity, меняем цвет текста)
        for i in range(limit):
            item = root.child(i)
            orig_fg = item.foreground(0).color()
            # Сохраняем цвет
            item.setData(0, Qt.ItemDataRole.UserRole + 2, orig_fg.name())
            # Делаем прозрачным
            faded = QColor(orig_fg)
            faded.setAlpha(0)
            item.setForeground(0, faded)

        if hasattr(self, '_tree_anim_timer'):
            self._tree_anim_timer.stop()
        self._tree_anim_timer = QTimer(self)
        self._tree_anim_timer.setInterval(35)
        self._tree_anim_timer.timeout.connect(self._tree_stagger_step)
        self._tree_anim_timer.start()

    def _tree_stagger_step(self):
        root = self.tree.invisibleRootItem()
        if self._tree_stagger_idx >= self._tree_stagger_limit:
            self._tree_anim_timer.stop()
            # Восстанавливаем цвета всех оставшихся
            for i in range(self._tree_stagger_limit):
                item = root.child(i)
                orig_name = item.data(0, Qt.ItemDataRole.UserRole + 2)
                if orig_name:
                    item.setForeground(0, QColor(orig_name))
            return
        item = root.child(self._tree_stagger_idx)
        if item:
            orig_name = item.data(0, Qt.ItemDataRole.UserRole + 2)
            if orig_name:
                item.setForeground(0, QColor(orig_name))
        self._tree_stagger_idx += 1

    def showEvent(self, event):
        """Главное окно появляется с fade-in."""
        super().showEvent(event)
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        eff = self.centralWidget().graphicsEffect()
        if not isinstance(eff, QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(self.centralWidget())
            self.centralWidget().setGraphicsEffect(eff)
        eff.setOpacity(0.0)
        self._show_fade_alpha = 0.0
        self._show_fade_timer = QTimer(self)
        self._show_fade_timer.setInterval(16)
        def _fade():
            self._show_fade_alpha = min(1.0, self._show_fade_alpha + 0.06)
            eff.setOpacity(self._show_fade_alpha)
            if self._show_fade_alpha >= 1.0:
                self._show_fade_timer.stop()
        self._show_fade_timer.timeout.connect(_fade)
        self._show_fade_timer.start()

    def _on_double_click(self, item, col):
        folder_path = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if folder_path:
            self.current_nav_path = folder_path
            self._sync_nav_ui()
            self._populate_tree()

    def _animate_label_change(self, label, new_text):
        """Fade-out → смена текста → fade-in для label."""
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        eff = label.graphicsEffect()
        if not isinstance(eff, QGraphicsOpacityEffect):
            eff = QGraphicsOpacityEffect(label)
            label.setGraphicsEffect(eff)
        alpha_h = [1.0]
        phase = [0]  # 0=out, 1=in
        t = QTimer(self)
        t.setInterval(16)
        def tick():
            if phase[0] == 0:
                alpha_h[0] = max(0.0, alpha_h[0] - 0.15)
                eff.setOpacity(alpha_h[0])
                if alpha_h[0] <= 0.0:
                    label.setText(new_text)
                    phase[0] = 1
            else:
                alpha_h[0] = min(1.0, alpha_h[0] + 0.1)
                eff.setOpacity(alpha_h[0])
                if alpha_h[0] >= 1.0:
                    t.stop()
        t.timeout.connect(tick)
        t.start()

    def _on_select_file(self):
        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]
        f_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not f_path:
            self.btn_replace.setEnabled(False)
            return

        self.current_selected_rel_path = f_path
        # Анимируем появление имени файла
        self._animate_label_change(self.lbl_filename, os.path.basename(f_path))
        self.btn_replace.setEnabled(True)
        self.btn_replace.set_breathing(True)  # живое свечение когда активна

        # Reset canvases
        self.orig_canvas.set_pil_image(None)
        self.orig_canvas.setText(LANG[self.current_lang]["loading"])
        self.sub_canvas.set_pil_image(None)
        self.sub_canvas.setText(LANG[self.current_lang]["loading"])
        self.lbl_size.setText("")

        # Start wave
        self._wave_progress = 0
        self._wave_tick = 0.0
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._wave_timer.start(30)

        # Start loader thread
        orig_path = os.path.join(self.base_path_edit.text(), f_path)
        sub_path = os.path.join(self.sub_path_edit.text(), f_path)
        if self._loader_thread and self._loader_thread.isRunning():
            self._loader_thread.done.disconnect()
            self._loader_thread.quit()
            self._loader_thread.wait(300)
        self._loader_thread = ImageLoaderThread(orig_path, sub_path)
        self._loader_thread.done.connect(self._on_load_done)
        self._loader_thread.start()

    def _tick_wave(self):
        self._wave_progress = min(self._wave_progress + 4, 98)
        self._wave_tick += 0.5
        self.progress_bar.setValue(int(self._wave_progress))

    def _on_load_done(self, orig_pil, sub_pil, sz):
        self._wave_timer.stop()
        self.progress_bar.setValue(100)
        self.progress_bar.hide()

        l = LANG.get(self.current_lang, LANG["EN"])

        if orig_pil:
            self.orig_canvas.set_pil_image(orig_pil)
        else:
            self.orig_canvas.set_pil_image(None)
            self.orig_canvas.setText(l["not_found"])

        if sub_pil:
            self.sub_canvas.set_pil_image(sub_pil)
        else:
            self.sub_canvas.set_pil_image(None)
            self.sub_canvas.setText(l["not_found"])

        self.lbl_size.setText(f"{l['size_lbl']}{sz}" if sz else "")


    # ── Theme / Lang ────────────────────────────────────────
    def _apply_theme(self):
        """Применяет Retrowave тему (единственная тема)."""
        self._retro_bg.show()
        self._splitter.setStyleSheet(
            "QSplitter { background: transparent; }"
            f"QSplitter::handle {{ background-color: rgba(155,48,255,80); }}"
        )
        self.setStyleSheet(get_main_stylesheet() + """
            #LeftPanel  {
                background: transparent;
                border-right: 1px solid rgba(155,48,255,60);
            }
            #RightPanel { background: transparent; }
            #TopPanel   {
                background: transparent;
                border-bottom: 1px solid rgba(155,48,255,60);
            }
            QTreeWidget {
                background-color: transparent;
                border: 1px solid rgba(155,48,255,60);
            }
            QTreeWidget::branch { background-color: transparent; }
            QTreeWidget::item:hover { background-color: rgba(155,48,255,40); }
            #ImageCanvas { background-color: transparent; border: 1px solid rgba(155,48,255,60); }
            QLineEdit    { background-color: rgba(10,10,30,80); }
            QComboBox    { background-color: rgba(10,10,30,80); }
            QComboBox QAbstractItemView { background-color: rgba(18,18,42,220); }
            QScrollBar:vertical   { background: transparent; }
            QScrollBar:horizontal { background: transparent; }
            #NavButton    { background-color: transparent; }
            #BrowseButton { background-color: transparent; }
            #ClearButton  { background-color: transparent; }
            #EditorBtn    { background-color: transparent; }
            QProgressBar  { background-color: rgba(8,8,26,80); }
            #ReplaceButton:disabled { background: rgba(26,26,58,120); }
        """)


    def _change_lang(self, lang_code):
        if lang_code not in LANG:
            return
        self.current_lang = lang_code
        self._save_config()
        self._update_ui_lang()

    def _update_ui_lang(self):
        l = LANG.get(self.current_lang, LANG["EN"])
        self.setWindowTitle(l["title"])
        self.btn_scan.setText(l["scan_btn"])
        self.lbl_base.setText(l["base_mod"])
        self.lbl_sub.setText(l["sub_mod"])
        self.lbl_list.setText(l["file_label"])
        self.btn_replace.setText(l["start_replace"])
        self.btn_clear.setText(l["clear_btn"])
        self.btn_back.setText(l["back_btn"])
        self.search_edit.setPlaceholderText(l["search_hint"])
        self.lbl_orig_view.setText(l["orig_view"])
        self.lbl_sub_view.setText(l["sub_view"])
        if not self.current_selected_rel_path:
            self.lbl_filename.setText(l["select_file"])
        self._sync_nav_ui()

    # ── Editor / Replace ────────────────────────────────────
    def _open_image_editor(self):
        if not self.current_selected_rel_path:
            return
        src, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.dds *.tga)"
        )
        if not src:
            return
        dest = os.path.join(self.sub_path_edit.text(), self.current_selected_rel_path)
        base_img = os.path.join(self.base_path_edit.text(), self.current_selected_rel_path)
        l = LANG.get(self.current_lang, LANG["EN"])

        editor = ImageEditorPro(self, src, dest, base_img, l, self._on_editor_success)
        editor.exec()

    def _on_editor_success(self):
        dest = os.path.join(self.sub_path_edit.text(), self.current_selected_rel_path)
        if dest in self.image_cache:
            del self.image_cache[dest]
        self._populate_tree()

        # Немедленная перезагрузка превью: сбрасываем кэш и запускаем фоновый загрузчик
        if self.current_selected_rel_path:
            self.orig_canvas.set_pil_image(None)
            self.orig_canvas.setText(LANG[self.current_lang]["loading"])
            self.sub_canvas.set_pil_image(None)
            self.sub_canvas.setText(LANG[self.current_lang]["loading"])
            self.lbl_size.setText("")
            self._wave_progress = 0
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self._wave_timer.start(30)

            orig_path = os.path.join(self.base_path_edit.text(), self.current_selected_rel_path)
            sub_path  = os.path.join(self.sub_path_edit.text(),  self.current_selected_rel_path)
            if self._loader_thread and self._loader_thread.isRunning():
                self._loader_thread.done.disconnect()
                self._loader_thread.quit()
                self._loader_thread.wait(200)
            self._loader_thread = ImageLoaderThread(orig_path, sub_path)
            self._loader_thread.done.connect(self._on_load_done)
            self._loader_thread.start()

        l = LANG.get(self.current_lang, LANG["EN"])
        QMessageBox.information(self, l["success_title"], l["success_msg"])

    def closeEvent(self, event):
        """FIX: cleanly stop background thread on close to avoid crash/hang."""
        self._hover_timer.stop()
        self._wave_timer.stop()
        if self._hover_preview:
            self._hover_preview.close()
        if self._loader_thread and self._loader_thread.isRunning():
            try:
                self._loader_thread.done.disconnect()
            except Exception:
                pass
            self._loader_thread.quit()
            self._loader_thread.wait(500)
        super().closeEvent(event)


# ====================== ТОЧКА ВХОДА ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("HOI4_GFX_Studio")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Splash: показываем только если уже есть config (язык выбран ранее).
    # Если config нет — сразу откроется диалог выбора языка, splash не нужен.
    _show_splash = CONFIG_FILE.exists()
    splash = None
    if _show_splash:
        splash = QLabel()
        splash.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.FramelessWindowHint
            # WindowStaysOnTopHint убран — перекрывал диалог выбора языка
        )
        splash.setFixedSize(420, 180)
        splash.setStyleSheet(f"""
            QLabel {{
                background-color: {DARK_BG};
                color: {NEON_CYAN};
                font-family: 'Segoe UI', monospace;
                font-size: 22pt;
                font-weight: bold;
                border: 1px solid {NEON_PURPLE};
                border-radius: 10px;
                qproperty-alignment: AlignCenter;
                letter-spacing: 3px;
            }}
        """)
        splash.setText("HOI4 GFX STUDIO\n\nLoading...")
        screen_geo = app.primaryScreen().availableGeometry()
        splash.move(
            (screen_geo.width()  - splash.width())  // 2,
            (screen_geo.height() - splash.height()) // 2,
        )
        splash.show()
        app.processEvents()

    window = HOI4ModdingStudio()
    window.show()
    if splash:
        splash.close()
    sys.exit(app.exec())