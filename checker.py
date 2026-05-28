import os
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import threading
import platform
import ctypes
import json
import math
from pathlib import Path
import sys
import colorsys
import numpy as np

# ══════════════════════════════════════════════════════════════════
#  Встроенный DDS-компрессор (BC1/DXT1 и BC3/DXT5)
#  Работает без texconv и любых внешних утилит.
#  numpy-векторизация: ~30 мс на портрет 156x207.
# ══════════════════════════════════════════════════════════════════
_DDSD_CAPS=0x1; _DDSD_HEIGHT=0x2; _DDSD_WIDTH=0x4
_DDSD_LINEARSIZE=0x80000; _DDSD_PIXELFORMAT=0x1000
_DDSCAPS_TEXTURE=0x1000;  _DDPF_FOURCC=0x4

def _dds_rgb565_enc(rgb):
    r=(rgb[:,0].astype(np.uint16)>>3)&0x1F
    g=(rgb[:,1].astype(np.uint16)>>2)&0x3F
    b=(rgb[:,2].astype(np.uint16)>>3)&0x1F
    return (r<<11)|(g<<5)|b

def _dds_rgb565_dec(v):
    r=((v>>11)&0x1F).astype(np.float32)*(255./31)
    g=((v>>5) &0x3F).astype(np.float32)*(255./63)
    b=(v       &0x1F).astype(np.float32)*(255./31)
    return np.stack([r,g,b],axis=-1)

def _bc1(rgb):
    """BC1/DXT1 цвет: (N,16,3) uint8 -> (N,8) uint8"""
    N=len(rgb); f=rgb.astype(np.float32)
    c0=_dds_rgb565_enc(f.max(1).clip(0,255).astype(np.uint8))
    c1=_dds_rgb565_enc(f.min(1).clip(0,255).astype(np.uint8))
    sw=c0<c1; c0[sw],c1[sw]=c1[sw].copy(),c0[sw].copy()
    c0f=_dds_rgb565_dec(c0); c1f=_dds_rgb565_dec(c1)
    pal=np.stack([c0f,c1f,(2*c0f+c1f)/3,(c0f+2*c1f)/3],axis=1)
    diff=f[:,:,np.newaxis,:]-pal[:,np.newaxis,:,:]
    idx=(diff**2).sum(-1).argmin(-1).astype(np.uint32)
    sh=np.arange(16,dtype=np.uint32)*2; ip=(idx<<sh).sum(1)
    o=np.zeros((N,8),dtype=np.uint8)
    o[:,0]=c0&0xFF;o[:,1]=(c0>>8)&0xFF;o[:,2]=c1&0xFF;o[:,3]=(c1>>8)&0xFF
    o[:,4]=ip&0xFF;o[:,5]=(ip>>8)&0xFF;o[:,6]=(ip>>16)&0xFF;o[:,7]=(ip>>24)&0xFF
    return o

def _bc3a(a):
    """BC3/DXT5 альфа: (N,16) uint8 -> (N,8) uint8"""
    N=len(a); a0=a.max(1).astype(np.float32); a1=a.min(1).astype(np.float32)
    pal=np.stack([a0,a1,(6*a0+a1)/7,(5*a0+2*a1)/7,
                  (4*a0+3*a1)/7,(3*a0+4*a1)/7,(2*a0+5*a1)/7,(a0+6*a1)/7],axis=1)
    idx=(( a.astype(np.float32)[:,:,np.newaxis]-pal[:,np.newaxis,:])**2).argmin(-1).astype(np.uint64)
    pk=np.zeros(N,dtype=np.uint64)
    for i in range(16): pk|=(idx[:,i]&np.uint64(7))<<np.uint64(i*3)
    o=np.zeros((N,8),dtype=np.uint8)
    o[:,0]=a0.astype(np.uint8); o[:,1]=a1.astype(np.uint8)
    for b in range(6): o[:,2+b]=(pk>>np.uint64(b*8))&np.uint64(0xFF)
    return o

def compress_to_dds(img):
    """
    PIL Image -> DDS bytes (BC3/DXT5 или BC1/DXT1) без внешних утилит.
    Автовыбор: есть прозрачность -> DXT5, нет -> DXT1 (вдвое легче).
    """
    rgba=img.convert("RGBA"); w,h=rgba.size
    pw=(-w)%4; ph=(-h)%4
    if pw or ph:
        p=Image.new("RGBA",(w+pw,h+ph),(0,0,0,0)); p.paste(rgba,(0,0)); rgba=p
    W,H=rgba.size
    arr=np.array(rgba,dtype=np.uint8)
    N=(H//4)*(W//4)
    blk=arr.reshape(H//4,4,W//4,4,4).transpose(0,2,1,3,4).reshape(N,16,4)
    has_alpha=bool(blk[:,:,3].min()<255)
    if has_alpha:
        data=np.concatenate([_bc3a(blk[:,:,3]),_bc1(blk[:,:,:3])],axis=1); fcc=b'DXT5'; bsz=16
    else:
        data=_bc1(blk[:,:,:3]); fcc=b'DXT1'; bsz=8
    lin=max(1,(w+3)//4)*max(1,(h+3)//4)*bsz
    hdr=struct.pack('<4sI',b'DDS ',124)
    hdr+=struct.pack('<5I',_DDSD_CAPS|_DDSD_HEIGHT|_DDSD_WIDTH|_DDSD_PIXELFORMAT|_DDSD_LINEARSIZE,h,w,lin,0)
    hdr+=struct.pack('<I',1)+b'\x00'*44
    hdr+=struct.pack('<II4sIIIII',32,_DDPF_FOURCC,fcc,0,0,0,0,0)
    hdr+=struct.pack('<5I',_DDSCAPS_TEXTURE,0,0,0,0)
    return hdr+data.tobytes()

# ====================== КОНФИГУРАЦИЯ ======================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_FILE = BASE_DIR / "config.json"

# --- ПОЛНЫЙ СЛОВАРЬ ЛОКАЛИЗАЦИИ ---
LANG = {
    "RU": {
        "title": "GFX_TOOL PRO (Explorer Mode)", "base_mod": "Оригинальный мод:", "sub_mod": "Сабмод (Папка замены):",
        "browse": "Обзор...", "scan_btn": "Начать анализ GFX", "file_label": "Проводник GFX:",
        "search_hint": "Поиск...", "all_folders": "Все папки (Root)", "clear_btn": "X",
        "back_btn": "⬅ Назад", "theme_btn": "Сменить тему", "orig_view": "ОРИГИНАЛ",
        "sub_view": "ЗАМЕНА В САБМОДЕ", "not_found": "ФАЙЛ НЕ НАЙДЕН", "select_file": "Выберите файл",
        "start_replace": "START: Заменить / Добавить", "success_title": "Успешно",
        "success_msg": "Файл успешно заменен и обновлен!", "loading": "Загрузка...",
        "size_lbl": "Размер: ", "err_dir": "Ошибка: Сначала выберите папки!",
        "editor_title": "Редактор GFX", "editor_save": "Применить и Сохранить", "editor_preset": "Формат / Пресет:",
        "btn_fit": "Вместить (Fit)", "btn_fill": "Заполнить (Fill)", "btn_stretch": "Растянуть (Stretch)", 
        "zoom_lbl": "Зум: ", "img_missing": "ИЗОБРАЖЕНИЕ ОТСУТСТВУЕТ",
        "addon_mod": "Аддон (Доп. замены):", "addon_view": "АДДОН",
        "mode_sub": "Писать в Сабмод", "mode_addon": "Писать в Аддон",
        "err_addon": "Ошибка: Сначала выберите папку аддона!",
        "mode_auto": "АВТО", "mode_manual": "ВРУЧНУЮ",
        "mode1_hint": "Режим 1 — Мод + Сабмод", "mode2_hint": "Режим 2 — Мод + Сабмод + Аддон"
    },
    "EN": {
        "title": "GFX_TOOL PRO (Explorer Mode)", "base_mod": "Original Mod:", "sub_mod": "Submod (Target Folder):",
        "browse": "Browse...", "scan_btn": "Start GFX Analysis", "file_label": "GFX Explorer:",
        "search_hint": "Search...", "all_folders": "All folders (Root)", "clear_btn": "X",
        "back_btn": "⬅ Back", "theme_btn": "Toggle Theme", "orig_view": "ORIGINAL",
        "sub_view": "SUBMOD REPLACEMENT", "not_found": "FILE NOT FOUND", "select_file": "Select a file",
        "start_replace": "START: Replace / Add", "success_title": "Success",
        "success_msg": "File replaced and updated successfully!", "loading": "Loading...",
        "size_lbl": "Size: ", "err_dir": "Error: Select directories first!",
        "editor_title": "GFX Editor", "editor_save": "Apply & Save", "editor_preset": "Format / Preset:",
        "btn_fit": "Fit", "btn_fill": "Fill", "btn_stretch": "Stretch", 
        "zoom_lbl": "Zoom: ", "img_missing": "IMAGE MISSING",
        "addon_mod": "Addon (Extra replacements):", "addon_view": "ADDON",
        "mode_sub": "Write to Submod", "mode_addon": "Write to Addon",
        "err_addon": "Error: Select addon folder first!",
        "mode_auto": "AUTO", "mode_manual": "MANUAL",
        "mode1_hint": "Mode 1 — Mod + Submod", "mode2_hint": "Mode 2 — Mod + Submod + Addon"
    },
    "JA": { "title": "GFX_TOOL PRO", "base_mod": "元モッド:", "sub_mod": "サブモッド:", "browse": "参照...", "scan_btn": "解析開始", "file_label": "エクスプローラー:", "search_hint": "検索...", "all_folders": "すべてのフォルダ", "clear_btn": "X", "back_btn": "⬅ 戻る", "theme_btn": "テーマ", "orig_view": "オリジナル", "sub_view": "置換", "not_found": "未検出", "select_file": "選択", "start_replace": "開始", "success_title": "成功", "success_msg": "成功！", "loading": "読み込み...", "size_lbl": "サイズ: ", "err_dir": "エラー！", "btn_fit": "合わせる", "btn_fill": "埋める", "btn_stretch": "伸ばす", "zoom_lbl": "ズーム: ", "img_missing": "画像なし", "addon_mod": "アドオン:", "addon_view": "アドオン", "mode_sub": "サブモッドに書き込む", "mode_addon": "アドオンに書き込む", "err_addon": "エラー！アドオンフォルダを選択してください", "mode_auto": "自動", "mode_manual": "手動", "mode1_hint": "モード1: Mod+Sub", "mode2_hint": "モード2: Mod+Sub+Addon", "editor_title": "GFX エディター", "editor_save": "適用して保存", "editor_preset": "フォーマット / プリセット:" },
    "KO": { "title": "GFX_TOOL PRO", "base_mod": "원본 모드:", "sub_mod": "서브모드:", "browse": "찾아보기...", "scan_btn": "분석 시작", "file_label": "탐색기:", "search_hint": "검색...", "all_folders": "모든 폴더", "clear_btn": "X", "back_btn": "뒤로", "theme_btn": "테마", "orig_view": "원본", "sub_view": "교체", "not_found": "찾을 수 없음", "select_file": "선택", "start_replace": "시작", "success_title": "성공", "success_msg": "성공!", "loading": "로딩...", "size_lbl": "크기: ", "err_dir": "오류!", "btn_fit": "맞춤", "btn_fill": "채우기", "btn_stretch": "늘리기", "zoom_lbl": "확대: ", "img_missing": "이미지 없음", "addon_mod": "애드온:", "addon_view": "애드온", "mode_sub": "서브모드에 쓰기", "mode_addon": "애드온에 쓰기", "err_addon": "오류! 애드온 폴더를 선택하세요", "mode_auto": "자동", "mode_manual": "수동", "mode1_hint": "모드1: Mod+Sub", "mode2_hint": "모드2: Mod+Sub+Addon", "editor_title": "GFX 편집기", "editor_save": "적용 및 저장", "editor_preset": "형식 / 프리셋:" },
    "DE": { "title": "GFX_TOOL PRO", "base_mod": "Original-Mod:", "sub_mod": "Submod:", "browse": "Durchsuchen...", "scan_btn": "Analyse starten", "file_label": "GFX-Explorer:", "search_hint": "Suchen...", "all_folders": "Alle Ordner", "clear_btn": "X", "back_btn": "⬅ Zurück", "theme_btn": "Thema", "orig_view": "ORIGINAL", "sub_view": "ERSATZ", "not_found": "NICHT GEFUNDEN", "select_file": "Datei wählen", "start_replace": "START", "success_title": "Erfolg", "success_msg": "Erfolgreich!", "loading": "Laden...", "size_lbl": "Größe: ", "err_dir": "Fehler!", "btn_fit": "Anpassen", "btn_fill": "Füllen", "btn_stretch": "Strecken", "zoom_lbl": "Zoom: ", "img_missing": "BILD FEHLT", "addon_mod": "Addon:", "addon_view": "ADDON", "mode_sub": "In Submod schreiben", "mode_addon": "In Addon schreiben", "err_addon": "Fehler! Addon-Ordner wählen!", "mode_auto": "AUTO", "mode_manual": "MANUELL", "mode1_hint": "Modus 1: Mod+Sub", "mode2_hint": "Modus 2: Mod+Sub+Addon", "editor_title": "GFX-Editor", "editor_save": "Anwenden & Speichern", "editor_preset": "Format / Vorlage:" },
    "FR": { "title": "GFX_TOOL PRO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Parcourir...", "scan_btn": "Analyser", "file_label": "Explorateur GFX:", "search_hint": "Rechercher...", "all_folders": "Tous les dossiers", "clear_btn": "X", "back_btn": "⬅ Retour", "theme_btn": "Thème", "orig_view": "ORIGINAL", "sub_view": "REMPLACEMENT", "not_found": "NON TROUVÉ", "select_file": "Choisir", "start_replace": "START", "success_title": "Succès", "success_msg": "Réussi !", "loading": "Chargement...", "size_lbl": "Taille: ", "err_dir": "Erreur !", "btn_fit": "Ajuster", "btn_fill": "Remplir", "btn_stretch": "Étirer", "zoom_lbl": "Zoom: ", "img_missing": "IMAGE MANQUANTE", "addon_mod": "Addon:", "addon_view": "ADDON", "mode_sub": "Écrire dans Submod", "mode_addon": "Écrire dans Addon", "err_addon": "Erreur ! Choisir dossier addon !", "mode_auto": "AUTO", "mode_manual": "MANUEL", "mode1_hint": "Mode 1: Mod+Sub", "mode2_hint": "Mode 2: Mod+Sub+Addon", "editor_title": "Éditeur GFX", "editor_save": "Appliquer & Enregistrer", "editor_preset": "Format / Préréglage:" },
    "ES": { "title": "GFX_TOOL PRO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Examinar...", "scan_btn": "Analizar", "file_label": "Explorador GFX:", "search_hint": "Buscar...", "all_folders": "Todas las carpetas", "clear_btn": "X", "back_btn": "⬅ Atrás", "theme_btn": "Tema", "orig_view": "ORIGINAL", "sub_view": "REEMPLAZO", "not_found": "NO ENCONTRADO", "select_file": "Seleccionar", "start_replace": "START", "success_title": "Éxito", "success_msg": "¡Éxito!", "loading": "Cargando...", "size_lbl": "Tamaño: ", "err_dir": "¡Error!", "btn_fit": "Ajustar", "btn_fill": "Llenar", "btn_stretch": "Estirar", "zoom_lbl": "Zoom: ", "img_missing": "IMAGEN FALTA", "addon_mod": "Addon:", "addon_view": "ADDON", "mode_sub": "Escribir en Submod", "mode_addon": "Escribir en Addon", "err_addon": "¡Error! Seleccione carpeta addon", "mode_auto": "AUTO", "mode_manual": "MANUAL", "mode1_hint": "Modo 1: Mod+Sub", "mode2_hint": "Modo 2: Mod+Sub+Addon", "editor_title": "Editor GFX", "editor_save": "Aplicar y Guardar", "editor_preset": "Formato / Preajuste:" },
    "PT": { "title": "GFX_TOOL PRO", "base_mod": "Mod Original:", "sub_mod": "Submod:", "browse": "Procurar...", "scan_btn": "Analisar", "file_label": "Explorador GFX:", "search_hint": "Pesquisar...", "all_folders": "Todas as pastas", "clear_btn": "X", "back_btn": "⬅ Voltar", "theme_btn": "Tema", "orig_view": "ORIGINAL", "sub_view": "SUBSTITUIÇÃO", "not_found": "NÃO ENCONTRADO", "select_file": "Selecionar", "start_replace": "START", "success_title": "Sucesso", "success_msg": "Sucesso!", "loading": "Carregando...", "size_lbl": "Tamanho: ", "err_dir": "Erro!", "btn_fit": "Ajustar", "btn_fill": "Preencher", "btn_stretch": "Esticar", "zoom_lbl": "Zoom: ", "img_missing": "IMAGEM FALTA", "addon_mod": "Addon:", "addon_view": "ADDON", "mode_sub": "Gravar no Submod", "mode_addon": "Gravar no Addon", "err_addon": "Erro! Selecione pasta addon!", "mode_auto": "AUTO", "mode_manual": "MANUAL", "mode1_hint": "Modo 1: Mod+Sub", "mode2_hint": "Modo 2: Mod+Sub+Addon", "editor_title": "Editor GFX", "editor_save": "Aplicar e Salvar", "editor_preset": "Formato / Predefinição:" },
    "CN": { "title": "GFX_TOOL PRO", "base_mod": "原模组:", "sub_mod": "子模组:", "browse": "浏览...", "scan_btn": "分析", "file_label": "GFX 资源管理器:", "search_hint": "搜索...", "all_folders": "所有文件夹", "clear_btn": "X", "back_btn": "⬅ 返回", "theme_btn": "切换主题", "orig_view": "原图", "sub_view": "替换", "not_found": "未找到", "select_file": "选择文件", "start_replace": "开始", "success_title": "成功", "success_msg": "成功！", "loading": "加载中...", "size_lbl": "尺寸: ", "err_dir": "错误！", "btn_fit": "适应", "btn_fill": "填充", "btn_stretch": "拉伸", "zoom_lbl": "缩放: ", "img_missing": "缺少图像", "addon_mod": "附加模组:", "addon_view": "附加", "mode_sub": "写入子模组", "mode_addon": "写入附加", "err_addon": "错误！请选择附加文件夹", "mode_auto": "自动", "mode_manual": "手动", "mode1_hint": "模式1: Mod+Sub", "mode2_hint": "模式2: Mod+Sub+Addon", "editor_title": "GFX 编辑器", "editor_save": "应用并保存", "editor_preset": "格式 / 预设:" }
}

# --- ТЕМЫ ОФОРМЛЕНИЯ С ПОЛУПРОЗРАЧНОСТЬЮ ---
THEMES = {
    "light": {
        "bg": "#f0f4f8", "fg": "#1a1a1a", "panel_bg": "#ffffff", "panel_accent": "#d9f0fc",
        "accent": "#00A4EF", "accent_hover": "#0078D4", "accent_fg": "#ffffff", "border": "#d1d5db",
        "tree_bg": "#ffffff", "tree_fg": "#000000", "tree_select": "#e1f5fe",
        "success_fg": "#2e7d32", "fail_fg": "#c62828", "canvas_bg": "#f9fafb",
        "btn_bg": "#e5e7eb", "btn_hover": "#d1d5db"
    },
    "dark": {
        "bg": "#0f0f0f", "fg": "#e0e0e0", "panel_bg": "#1c1c1c", "panel_accent": "#0a223f",
        "accent": "#1565C0", "accent_hover": "#1976D2", "accent_fg": "#ffffff", "border": "#2d2d2d",
        "tree_bg": "#1c1c1c", "tree_fg": "#ffffff", "tree_select": "#0d47a1",
        "success_fg": "#a5d6a7", "fail_fg": "#ef9a9a", "canvas_bg": "#111111",
        "btn_bg": "#2d2d2d", "btn_hover": "#3d3d3d"
    }
}

# --- ПРЕСЕТЫ ДЛЯ HOI4 ---
HOI4_PRESETS = {
    "Leader Portrait (156x207)": (156, 207),
    "Event Picture (156x225)": (156, 225),
    "National Focus (80x130)": (80, 130),
    "Idea/Minister (60x68)": (60, 68),
    "Custom (Free)": None
}

# --- ЭФФЕКТЫ WINDOWS 11 ---
def apply_windows_11_effect(window, is_dark_mode, alpha=0.96):
    window.update_idletasks()
    if platform.system() == "Windows" and int(platform.release()) >= 10:
        try:
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(2 if is_dark_mode else 0)), 4)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(ctypes.c_int(3)), 4)
        except Exception:
            pass
    window.attributes("-alpha", alpha)

def bind_hover_effect(widget, default_bg, hover_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))

class LanguageSelector(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = "RU"
        self.title("Select Language")
        width, height = 520, 800
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(screen_w // 2) - (width // 2)}+{(screen_h // 2) - (height // 2)}")
        self.configure(bg="#0a0a0a")
        apply_windows_11_effect(self, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set() 
        self.resizable(False, False)
        tk.Label(self, text="Select your language", bg="#0a0a0a", fg="#00A4EF", font=("Segoe UI", 24, "bold"), pady=40).pack()
        container = tk.Frame(self, bg="#0a0a0a")
        container.pack(pady=10)
        langs = [("РУССКИЙ", "RU"), ("ENGLISH", "EN"), ("日本語", "JA"), ("한국어", "KO"),
                 ("DEUTSCH", "DE"), ("FRANÇAIS", "FR"), ("ESPAÑOL", "ES"), ("PORTUGUÊS", "PT"), ("中文", "CN")]
        for name, code in langs:
            btn = tk.Button(container, text=name, width=35, font=("Segoe UI", 12, "bold"),
                            bg="#161616", fg="white", activebackground="#00A4EF", activeforeground="white", 
                            cursor="hand2", bd=1, relief="solid", pady=10, command=lambda c=code: self.set_lang(c))
            bind_hover_effect(btn, "#161616", "#00A4EF")
            btn.pack(pady=5)
            
    def set_lang(self, code):
        self.result = code
        self.destroy()
    def on_close(self):
        sys.exit()

# --- ВСТРОЕННЫЙ РЕДАКТОР ИЗОБРАЖЕНИЙ ---
class ImageEditorPro(tk.Toplevel):
    def __init__(self, parent, src_img_path, dest_img_path, base_img_path, lang_dict, theme_colors, callback):
        super().__init__(parent)
        self.title(lang_dict.get("editor_title", "Image Editor"))
        self.configure(bg=theme_colors["bg"])
        self.resizable(True, True)
        # alpha=1.0 — редактор полностью непрозрачный, не просвечивает главный экран
        apply_windows_11_effect(self, theme_colors["bg"] == "#0f0f0f", alpha=1.0)

        self.src_img_path  = src_img_path
        self.dest_img_path = dest_img_path
        self.base_img_path = base_img_path
        self.callback  = callback
        self.theme     = theme_colors
        self.lang      = lang_dict

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

        self.scale_x  = 1.0
        self.scale_y  = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.drag_data = {"x": 0, "y": 0}

        self.build_ui()
        self._center_on_parent(parent)
        # do_fill после того как canvas получил реальные размеры
        self.after(50, self._initial_fit)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        w, h = 960, 720
        self.minsize(700, 500)
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = min(x, sw - w)
        y = min(y, sh - h)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _initial_fit(self):
        """Вызывается после рендера — canvas уже имеет реальные размеры."""
        self.do_fill()
        # Перерисовывать при изменении размера окна
        self.canvas.bind("<Configure>", lambda e: self.update_canvas())

    def _get_base_dims(self):
        try:
            if os.path.exists(self.base_img_path):
                # Исправлено: безопасное чтение размера
                with Image.open(self.base_img_path) as img:
                    return img.width, img.height
        except Exception:
            pass
        return None, None

    def build_ui(self):
        # ── Toolbar (2 строки) ──────────────────────────────────
        toolbar = tk.Frame(self, bg=self.theme["panel_bg"], pady=6, padx=10)
        toolbar.pack(fill=tk.X)

        # Строка 1: пресет + Fit/Fill/Stretch + зум
        row1 = tk.Frame(toolbar, bg=self.theme["panel_bg"])
        row1.pack(fill=tk.X, pady=(0, 4))

        tk.Label(row1, text=self.lang.get("editor_preset", "Preset:"),
                 bg=self.theme["panel_bg"], fg=self.theme["fg"],
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        self.preset_var = tk.StringVar(value=self.current_preset)
        self.preset_combo = ttk.Combobox(row1, textvariable=self.preset_var,
                                         values=list(self.presets.keys()),
                                         state="readonly", width=28)
        self.preset_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.preset_combo.bind("<<ComboboxSelected>>", self.on_preset_change)

        btn_opts = {"font": ("Segoe UI", 9, "bold"), "bg": self.theme["btn_bg"],
                    "fg": self.theme["fg"], "relief": "flat",
                    "padx": 12, "pady": 4, "cursor": "hand2"}
        self.btn_fit     = tk.Button(row1, text=self.lang.get("btn_fit",     "Fit"),     command=self.do_fit,     **btn_opts)
        self.btn_fill    = tk.Button(row1, text=self.lang.get("btn_fill",    "Fill"),    command=self.do_fill,    **btn_opts)
        self.btn_stretch = tk.Button(row1, text=self.lang.get("btn_stretch", "Stretch"), command=self.do_stretch, **btn_opts)
        for btn in [self.btn_fit, self.btn_fill, self.btn_stretch]:
            btn.pack(side=tk.LEFT, padx=3)
            bind_hover_effect(btn, self.theme["btn_bg"], self.theme["btn_hover"])

        self.zoom_lbl = tk.Label(row1,
                                 text=self.lang.get("zoom_lbl", "Zoom: ") + "100%",
                                 bg=self.theme["panel_bg"], fg=self.theme["accent"],
                                 font=("Segoe UI", 9, "bold"))
        self.zoom_lbl.pack(side=tk.LEFT, padx=18)

        # Строка 2: кнопка сохранения во всю ширину
        row2 = tk.Frame(toolbar, bg=self.theme["panel_bg"])
        row2.pack(fill=tk.X)

        self.btn_save = tk.Button(
            row2,
            text=self.lang.get("editor_save", "Apply & Save"),
            font=("Segoe UI", 11, "bold"),
            bg=self.theme["accent"], fg=self.theme["accent_fg"],
            relief="flat", pady=8, cursor="hand2",
            command=self.save_image)
        bind_hover_effect(self.btn_save, self.theme["accent"], self.theme["accent_hover"])
        self.btn_save.pack(fill=tk.X)

        # ── Canvas ──────────────────────────────────────────────
        self.canvas_frame = tk.Frame(self, bg=self.theme["canvas_bg"])
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 12))

        self.canvas = tk.Canvas(self.canvas_frame, bg=self.theme["canvas_bg"],
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>",     self.on_drag_motion)
        self.canvas.bind("<MouseWheel>",    self.on_zoom)
        self.canvas.bind("<Button-4>",      self.on_zoom)
        self.canvas.bind("<Button-5>",      self.on_zoom)

    def get_target_dims(self):
        target_size = self.presets.get(self.current_preset)
        if target_size:
            return target_size
        return self.original_img.width, self.original_img.height

    def do_fit(self):
        tw, th = self.get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        s = min(tw/w, th/h)
        self.scale_x = self.scale_y = s
        self.offset_x, self.offset_y = 0, 0
        self.update_canvas()

    def do_fill(self):
        tw, th = self.get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        s = max(tw/w, th/h)
        self.scale_x = self.scale_y = s
        self.offset_x, self.offset_y = 0, 0
        self.update_canvas()

    def do_stretch(self):
        tw, th = self.get_target_dims()
        w, h = self.original_img.width, self.original_img.height
        if w == 0 or h == 0: return
        self.scale_x = tw/w
        self.scale_y = th/h
        self.offset_x, self.offset_y = 0, 0
        self.update_canvas()

    def on_preset_change(self, event):
        self.current_preset = self.preset_var.get()
        self.do_fill()
        # do_fill() already calls update_canvas() internally — no duplicate call needed

    def on_drag_start(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag_motion(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.offset_x += dx
        self.offset_y += dy
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.update_canvas()

    def on_zoom(self, event):
        zoom_factor = 1.1 if event.delta > 0 or event.num == 4 else 0.9
        self.scale_x *= zoom_factor
        self.scale_y *= zoom_factor
        self.update_canvas()

    def update_canvas(self):
        self.canvas.delete("all")
        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        
        if c_width <= 1: c_width, c_height = 800, 600

        target_size = self.presets.get(self.current_preset)
        if target_size:
            tw, th = target_size
        else:
            tw, th = int(self.original_img.width * self.scale_x), int(self.original_img.height * self.scale_y)

        cx, cy = c_width // 2, c_height // 2
        
        sw, sh = int(self.original_img.width * self.scale_x), int(self.original_img.height * self.scale_y)
        if sw > 0 and sh > 0:
            resized = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(resized)
            
            img_x = cx - (tw // 2) + (tw - sw) // 2 + self.offset_x
            img_y = cy - (th // 2) + (th - sh) // 2 + self.offset_y
            self.canvas.create_image(img_x, img_y, image=self.tk_img, anchor="nw")

        if target_size:
            rect_x1, rect_y1 = cx - tw // 2, cy - th // 2
            rect_x2, rect_y2 = cx + tw // 2, cy + th // 2
            
            self.canvas.create_rectangle(0, 0, c_width, rect_y1, fill="#000000", stipple="gray50", outline="")
            self.canvas.create_rectangle(0, rect_y2, c_width, c_height, fill="#000000", stipple="gray50", outline="")
            self.canvas.create_rectangle(0, rect_y1, rect_x1, rect_y2, fill="#000000", stipple="gray50", outline="")
            self.canvas.create_rectangle(rect_x2, rect_y1, c_width, rect_y2, fill="#000000", stipple="gray50", outline="")
            
            self.canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, outline=self.theme["accent"], width=3, dash=(5, 5))

        avg_zoom = int((self.scale_x + self.scale_y) / 2.0 * 100)
        self.zoom_lbl.config(text=f"{self.lang.get('zoom_lbl', 'Zoom: ')}{avg_zoom}%")

    def save_image(self):
        target_size = self.presets.get(self.current_preset)

        if target_size:
            tw, th = target_size
            final_img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            sw = int(self.original_img.width  * self.scale_x)
            sh = int(self.original_img.height * self.scale_y)
            resized = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)
            paste_x = (tw - sw) // 2 + self.offset_x
            paste_y = (th - sh) // 2 + self.offset_y
            final_img.paste(resized, (paste_x, paste_y),
                            resized if resized.mode == "RGBA" else None)
        else:
            sw = int(self.original_img.width  * self.scale_x)
            sh = int(self.original_img.height * self.scale_y)
            final_img = self.original_img.resize((sw, sh), Image.Resampling.LANCZOS)

        dest_dir = os.path.dirname(self.dest_img_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        # Защита от нулевых размеров при экстремальном зуме
        if sw <= 0 or sh <= 0:
            messagebox.showerror("Error", "Image size is zero — adjust zoom and try again.")
            return
        try:
            ext = os.path.splitext(self.dest_img_path)[1].lower()
            if ext == ".dds":
                # Встроенный BC1/DXT1 + BC3/DXT5 компрессор — без внешних утилит
                dds_bytes = compress_to_dds(final_img)
                with open(self.dest_img_path, "wb") as f:
                    f.write(dds_bytes)
            elif ext == ".tga":
                final_img.save(self.dest_img_path, format="TGA")
            elif ext in (".jpg", ".jpeg"):
                # JPEG не поддерживает альфу
                final_img.convert("RGB").save(self.dest_img_path, format="JPEG", quality=95)
            else:
                final_img.save(self.dest_img_path)

            self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

class HOI4ModdingStudio:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # скрыть до готовности

        self.image_cache = {}
        self.tk_cache = {}
        self._cache_lock = threading.Lock()   # защита image_cache от гонки потоков
        self.current_lang = "RU"
        self.current_theme = "dark"
        self.load_config()

        self.root.title(LANG[self.current_lang]["title"])
        self.window_width  = 1340
        self.window_height = 780
        self.root.minsize(900, 600)
        self.center_window()

        # Показать ПОСЛЕ позиционирования, вывести поверх
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))
        
        self.base_path  = tk.StringVar()
        self.sub_path   = tk.StringVar()
        self.addon_path = tk.StringVar()
        self.write_mode = tk.StringVar(value="sub")
        self._mode_is_manual = False  # False=авто, True=вручную

        # Восстановить пути из config
        self.base_path.set(getattr(self, '_saved_base',  ''))
        self.sub_path.set(getattr(self, '_saved_sub',   ''))
        self.addon_path.set(getattr(self, '_saved_addon', ''))
        # Автосохранение при изменении
        for _v in (self.base_path, self.sub_path, self.addon_path):
            _v.trace_add("write", lambda *_: self.save_config())
        self.files_data = [] 
        self.last_scanned_dirs = []
        self.current_nav_path = "gfx" 
        self.current_selected_rel_path = None
        self._search_timer = None 
        
        self._animating_wave = False
        self.load_progress = 0
        self.wave_tick = 0
        self._temp_io_pil = None
        self._temp_isub_pil = None
        self._temp_iaddon_pil = None
        self._temp_sz = None
        # Generation counter: each new file selection increments it.
        # animate_wave checks its own generation; stale loops self-cancel.
        self._load_gen = 0
        
        self.hover_timer = None
        self.preview_window = None
        self.hovered_item = None
        
        self.themed_frames = []
        self.themed_labels = []
        self.accent_frames = []
        self.accent_labels = []

        self.setup_styles()
        self.build_ui()
        self.apply_theme()
        self._neon_after_id = None
        self.apply_neon_effect()
        self._bind_hotkeys()
        self._auto_detect_mode()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Корректное закрытие: отменяем все after-колбэки перед уничтожением окна."""
        if self._neon_after_id:
            self.root.after_cancel(self._neon_after_id)
        self._animating_wave = False
        self.root.destroy()

    def _bind_hotkeys(self):
        self.root.bind("<F5>",        lambda e: self.scan_files())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())
        self.root.bind("<Escape>",    lambda e: self.clear_search())
        self.root.bind("<BackSpace>", lambda e: self.go_back())

    def center_window(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(self.window_width,  sw - 40)
        h = min(self.window_height, sh - 80)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 30)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def load_config(self):
        self._saved_base = self._saved_sub = self._saved_addon = ''
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("language") in LANG: self.current_lang = data["language"]
                    if data.get("theme") in THEMES:  self.current_theme = data["theme"]
                    self._saved_base  = data.get("base_path",  "")
                    self._saved_sub   = data.get("sub_path",   "")
                    self._saved_addon = data.get("addon_path", "")
                    return
            except Exception: pass
        selector = LanguageSelector(self.root)
        self.root.wait_window(selector)
        self.current_lang = selector.result
        self.save_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "language":   self.current_lang,
                    "theme":      self.current_theme,
                    "base_path":  self.base_path.get()  if hasattr(self, 'base_path')  else "",
                    "sub_path":   self.sub_path.get()   if hasattr(self, 'sub_path')   else "",
                    "addon_path": self.addon_path.get() if hasattr(self, 'addon_path') else "",
                }, f, ensure_ascii=False, indent=2)
        except Exception: pass

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=35, borderwidth=0)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def apply_neon_effect(self):
        self.neon_hue = getattr(self, 'neon_hue', 0)
        self.neon_hue = (self.neon_hue + 0.005) % 1.0
        
        rgb = colorsys.hsv_to_rgb(self.neon_hue, 0.8, 1.0)
        hex_color = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        
        if hasattr(self, 'neon_line'):
            self.neon_line.configure(bg=hex_color)
        else:
            self.neon_line = tk.Frame(self.root_frame, height=3, bg=hex_color)
            self.neon_line.pack(side=tk.TOP, fill=tk.X, before=self.root_frame.winfo_children()[0])
            
        self._neon_after_id = self.root.after(40, self.apply_neon_effect)

    # ─── УМНЫЙ РЕЖИМ ────────────────────────────────────────────
    def _auto_detect_mode(self):
        if self._mode_is_manual: return
        if self.addon_path.get().strip():
            self.write_mode.set("addon")
        else:
            self.write_mode.set("sub")
        self._refresh_mode_ui()

    def _on_manual_mode(self):
        self._mode_is_manual = True
        self._refresh_mode_ui()

    def _reset_to_auto(self):
        self._mode_is_manual = False
        self._auto_detect_mode()

    def _refresh_mode_ui(self):
        if not hasattr(self, 'lbl_mode_badge'): return
        l   = LANG.get(self.current_lang, LANG["EN"])
        thm = THEMES[self.current_theme]
        is_manual = self._mode_is_manual
        is_addon  = self.write_mode.get() == "addon"
        badge_text = f"◆ {l.get('mode_manual','MANUAL')}" if is_manual else f"◆ {l.get('mode_auto','AUTO')}"
        badge_fg   = thm["fail_fg"] if is_manual else thm["success_fg"]
        hint_text  = l.get("mode2_hint","") if is_addon else l.get("mode1_hint","")
        self.lbl_mode_badge.configure(text=badge_text, fg=badge_fg, bg=thm["panel_accent"])
        self.lbl_mode_hint.configure(text=hint_text, bg=thm["panel_accent"], fg=thm["fg"])
        self.radio_sub.configure(bg=thm["panel_accent"],   fg=thm["fg"],
                                 selectcolor=thm["panel_bg"], activebackground=thm["panel_accent"])
        self.radio_addon.configure(bg=thm["panel_accent"], fg=thm["fg"],
                                   selectcolor=thm["panel_bg"], activebackground=thm["panel_accent"])
        if is_manual:
            self.btn_reset_mode.configure(bg=thm["btn_bg"], fg=thm["accent"])
            self.btn_reset_mode.pack(side=tk.LEFT)
        else:
            self.btn_reset_mode.pack_forget()

    # ─── АСИНХРОННОЕ СКАНИРОВАНИЕ ───────────────────────────────
    def scan_files(self):
        b_root = self.base_path.get()
        if not b_root or not os.path.exists(os.path.join(b_root, "gfx")):
            messagebox.showerror("Error", LANG[self.current_lang]["err_dir"])
            return
        self.btn_scan.config(state=tk.DISABLED, text="⏳ ...")
        threading.Thread(target=self._bg_scan, args=(b_root,), daemon=True).start()

    def _bg_scan(self, b_root):
        def fast_walk(path):
            try:
                for entry in os.scandir(path):
                    if entry.is_dir(): yield from fast_walk(entry.path)
                    elif entry.name.lower().endswith(('.dds','.tga','.png','.jpg')):
                        yield os.path.relpath(entry.path, b_root)
            except PermissionError: pass
        files    = sorted(list(fast_walk(os.path.join(b_root, "gfx"))))
        # Fix: top_dirs should be the first-level subdirs inside gfx (e.g. "gfx\portraits"),
        # not just "gfx" for every file.
        top_dirs = sorted({os.sep.join(f.split(os.sep)[:2]) for f in files if f.count(os.sep) >= 1})
        self.root.after(0, lambda: self._on_scan_done(files, top_dirs))

    def _on_scan_done(self, files, top_dirs):
        self.files_data = files
        self.last_scanned_dirs = top_dirs
        self.btn_scan.config(state=tk.NORMAL, text=LANG[self.current_lang]["scan_btn"])
        self.sync_navigation_ui()
        self.populate_treeview()

    def apply_theme(self):
        thm = THEMES[self.current_theme]
        self.root.configure(bg=thm["bg"])
        apply_windows_11_effect(self.root, self.current_theme == "dark")
        
        for f in self.themed_frames: 
            if f.winfo_exists(): f.configure(bg=thm["panel_bg"])
        for f in self.accent_frames:
            if f.winfo_exists(): f.configure(bg=thm["panel_accent"])
        self.root_frame.configure(bg=thm["bg"])
        for l in self.themed_labels: 
            if l.winfo_exists(): l.configure(bg=thm["panel_bg"], fg=thm["fg"])
        for l in self.accent_labels:
            if l.winfo_exists(): l.configure(bg=thm["panel_accent"], fg=thm["fg"])
        
        self.btn_scan.configure(bg=thm["accent"], fg=thm["accent_fg"], activebackground=thm["accent_hover"])
        bind_hover_effect(self.btn_scan, thm["accent"], thm["accent_hover"])
        
        self.btn_theme.configure(bg=thm["btn_bg"], fg=thm["fg"], activebackground=thm["btn_hover"])
        bind_hover_effect(self.btn_theme, thm["btn_bg"], thm["btn_hover"])
        
        self.btn_replace.configure(bg=thm["accent"], fg=thm["accent_fg"], activebackground=thm["accent_hover"])
        bind_hover_effect(self.btn_replace, thm["accent"], thm["accent_hover"])
        
        self.btn_clear.configure(bg=thm["btn_bg"], fg=thm["fg"])
        bind_hover_effect(self.btn_clear, thm["btn_bg"], thm["btn_hover"])
        
        self.btn_back.configure(bg=thm["btn_bg"], fg=thm["fg"])
        bind_hover_effect(self.btn_back, thm["btn_bg"], thm["btn_hover"])
        
        self.orig_canvas.configure(bg=thm["canvas_bg"], fg=thm["fg"])
        self.sub_canvas.configure(bg=thm["canvas_bg"], fg=thm["fg"])
        self.addon_canvas.configure(bg=thm["canvas_bg"], fg=thm["accent"])
        self.lbl_nav.configure(bg=thm["panel_bg"], fg=thm["accent"])
        
        # Стилизация радиокнопок
        for rb in [self.radio_sub, self.radio_addon]:
            rb.configure(bg=thm["panel_accent"], fg=thm["fg"],
                         selectcolor=thm["panel_bg"], activebackground=thm["panel_accent"])
        self.btn_reset_mode.configure(bg=thm["btn_bg"], fg=thm["accent"],
                                      activebackground=thm["btn_hover"])

        self.style.configure("Treeview", background=thm["tree_bg"], foreground=thm["tree_fg"], fieldbackground=thm["tree_bg"])
        self.style.map("Treeview", background=[("selected", thm["tree_select"])])
        self.tree.tag_configure("exists",  foreground=thm["success_fg"])
        self.tree.tag_configure("missing", foreground=thm["fail_fg"])
        self.tree.tag_configure("addon",   foreground=thm["accent"])
        self.tree.tag_configure("folder",  foreground=thm["fg"], font=("Segoe UI", 10, "bold"))

        # Горячие клавиши
        for k_lbl, d_lbl, lang_key in getattr(self, 'hotkey_labels', []):
            if k_lbl.winfo_exists():
                k_lbl.configure(bg=thm["btn_bg"], fg=thm["accent"])
                d_lbl.configure(bg=thm["panel_accent"], fg=thm["fg"],
                                 text=LANG[self.current_lang].get(lang_key, ""))

        self._refresh_mode_ui()

    def build_ui(self):
        self.root_frame = tk.Frame(self.root)
        self.root_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(self.root_frame, pady=15, padx=20, bd=0)
        self.accent_frames.append(top_frame)
        top_frame.pack(fill=tk.X)

        right_group = tk.Frame(top_frame)
        self.accent_frames.append(right_group)
        right_group.pack(side=tk.RIGHT)

        self.btn_theme = tk.Button(right_group, text=LANG[self.current_lang]["theme_btn"], font=("Segoe UI", 9), relief="flat", padx=12, pady=6, cursor="hand2", command=self.toggle_theme)
        self.btn_theme.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Быстрый переключатель языка ---
        LANG_FLAGS = {
            "RU": "🇷🇺", "EN": "🇬🇧", "JA": "🇯🇵", "KO": "🇰🇷",
            "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸", "PT": "🇵🇹", "CN": "🇨🇳"
        }
        self.lang_combo = ttk.Combobox(
            right_group,
            values=[f"{LANG_FLAGS.get(k, '')} {k}" for k in LANG.keys()],
            width=8, state="readonly"
        )
        # Set current value with flag
        self.lang_combo.set(f"{LANG_FLAGS.get(self.current_lang, '')} {self.current_lang}")
        self.lang_combo.pack(side=tk.RIGHT, padx=10)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_lang_event)

        self.btn_scan = tk.Button(right_group, text=LANG[self.current_lang]["scan_btn"], font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=8, cursor="hand2", command=self.scan_files)
        self.btn_scan.pack(side=tk.RIGHT)

        grid_frame = tk.Frame(top_frame)
        self.accent_frames.append(grid_frame)
        grid_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_base = tk.Label(grid_frame, text=LANG[self.current_lang]["base_mod"], font=("Segoe UI", 8, "bold"))
        self.accent_labels.append(self.lbl_base)
        self.lbl_base.grid(row=0, column=0, sticky="w", pady=2)
        tk.Entry(grid_frame, textvariable=self.base_path, width=50, font=("Consolas", 10), relief="flat").grid(row=0, column=1, padx=10)
        ttk.Button(grid_frame, text="...", width=3, command=lambda: self.get_path(self.base_path)).grid(row=0, column=2)

        self.lbl_sub = tk.Label(grid_frame, text=LANG[self.current_lang]["sub_mod"], font=("Segoe UI", 8, "bold"))
        self.accent_labels.append(self.lbl_sub)
        self.lbl_sub.grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(grid_frame, textvariable=self.sub_path, width=50, font=("Consolas", 10), relief="flat").grid(row=1, column=1, padx=10)
        ttk.Button(grid_frame, text="...", width=3, command=lambda: self.get_path(self.sub_path)).grid(row=1, column=2)

        self.lbl_addon = tk.Label(grid_frame, text=LANG[self.current_lang]["addon_mod"], font=("Segoe UI", 8, "bold"))
        self.accent_labels.append(self.lbl_addon)
        self.lbl_addon.grid(row=2, column=0, sticky="w", pady=2)
        tk.Entry(grid_frame, textvariable=self.addon_path, width=50, font=("Consolas", 10), relief="flat").grid(row=2, column=1, padx=10)
        ttk.Button(grid_frame, text="...", width=3, command=lambda: self.get_path(self.addon_path)).grid(row=2, column=2)

        # --- Умный переключатель режима записи ---
        mode_frame = tk.Frame(grid_frame)
        self.accent_frames.append(mode_frame)
        mode_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.lbl_mode_badge = tk.Label(mode_frame, text="◆ АВТО",
                                       font=("Segoe UI", 8, "bold"), padx=6, pady=2)
        self.lbl_mode_badge.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_mode_hint = tk.Label(mode_frame, text="",
                                      font=("Segoe UI", 8, "italic"))
        self.lbl_mode_hint.pack(side=tk.LEFT, padx=(0, 12))

        self.radio_sub = tk.Radiobutton(mode_frame, text=LANG[self.current_lang]["mode_sub"],
                                        variable=self.write_mode, value="sub",
                                        font=("Segoe UI", 8), cursor="hand2", relief="flat",
                                        command=self._on_manual_mode)
        self.radio_addon = tk.Radiobutton(mode_frame, text=LANG[self.current_lang]["mode_addon"],
                                          variable=self.write_mode, value="addon",
                                          font=("Segoe UI", 8, "bold"), cursor="hand2", relief="flat",
                                          command=self._on_manual_mode)
        self.radio_sub.pack(side=tk.LEFT, padx=(0, 4))
        self.radio_addon.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_reset_mode = tk.Button(mode_frame, text="↺",
                                        font=("Segoe UI", 9, "bold"), relief="flat",
                                        padx=6, pady=1, cursor="hand2",
                                        command=self._reset_to_auto)
        # кнопка ↺ показывается только в ручном режиме — pack/forget в _refresh_mode_ui

        # Трейс: авто-переключение при изменении addon_path
        self.addon_path.trace_add("write", lambda *_: self._auto_detect_mode())

        main_pane = tk.PanedWindow(self.root_frame, orient=tk.HORIZONTAL, bd=0, sashwidth=6)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        left_col = tk.Frame(main_pane, padx=15, pady=15)
        self.themed_frames.append(left_col)
        
        self.lbl_list = tk.Label(left_col, text=LANG[self.current_lang]["file_label"], font=("Segoe UI", 11, "bold"))
        self.themed_labels.append(self.lbl_list)
        self.lbl_list.pack(anchor="w", pady=(0, 2))
        
        self.lbl_nav = tk.Label(left_col, text="gfx", font=("Consolas", 10, "bold"), anchor="w")
        self.themed_labels.append(self.lbl_nav)
        self.lbl_nav.pack(fill=tk.X, pady=(0, 10))
        
        search_frame = tk.Frame(left_col)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        self.themed_frames.append(search_frame)

        self.btn_back = tk.Button(search_frame, text=LANG[self.current_lang]["back_btn"], font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4, cursor="hand2", command=self.go_back)
        self.btn_back.pack(side=tk.LEFT, padx=(0, 5))
        
        self.folder_var = tk.StringVar()
        self.folder_combo = ttk.Combobox(search_frame, textvariable=self.folder_var, state="readonly", width=18)
        self.folder_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.folder_combo.bind("<<ComboboxSelected>>", self.on_combo_select)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.schedule_search())

        self.btn_clear = tk.Button(search_frame, text=LANG[self.current_lang]["clear_btn"], font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4, cursor="hand2", command=self.clear_search)
        self.btn_clear.pack(side=tk.LEFT, padx=(5, 0))

        tree_scroll = ttk.Scrollbar(left_col)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree = ttk.Treeview(left_col, show="tree", yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_select_file)
        self.tree.bind('<Double-1>', self.on_double_click)
        
        self.tree.bind("<Motion>", self.on_tree_hover)
        self.tree.bind("<Leave>", self.cancel_hover_preview)
        self.tree.bind("<ButtonPress-1>", self.cancel_hover_preview) 

        main_pane.add(left_col, width=450)

        right_col = tk.Frame(main_pane)
        self.themed_frames.append(right_col)
        
        self.lbl_filename = tk.Label(right_col, text=LANG[self.current_lang]["select_file"], font=("Segoe UI", 14, "bold"))
        self.themed_labels.append(self.lbl_filename)
        self.lbl_filename.pack(pady=15)

        viewer_frame = tk.Frame(right_col)
        self.themed_frames.append(viewer_frame)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.orig_canvas = tk.Label(viewer_frame, text=LANG[self.current_lang]["orig_view"], compound=tk.TOP, font=("Segoe UI", 10, "bold"))
        self.orig_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.sub_canvas = tk.Label(viewer_frame, text=LANG[self.current_lang]["sub_view"], compound=tk.TOP, font=("Segoe UI", 10, "bold"))
        self.sub_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.addon_canvas = tk.Label(viewer_frame, text=LANG[self.current_lang]["addon_view"], compound=tk.TOP, font=("Segoe UI", 10, "bold"))
        self.addon_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.lbl_size = tk.Label(right_col, text="", font=("Segoe UI", 10))
        self.themed_labels.append(self.lbl_size)
        self.lbl_size.pack(pady=10)

        btn_box = tk.Frame(right_col, pady=20)
        self.accent_frames.append(btn_box)
        btn_box.pack(fill=tk.X)

        self.btn_replace = tk.Button(btn_box, text=LANG[self.current_lang]["start_replace"], 
                                    font=("Segoe UI", 12, "bold"), relief="flat", padx=40, pady=12, cursor="hand2", 
                                    command=self.open_image_editor, state=tk.DISABLED)
        self.btn_replace.pack()

        main_pane.add(right_col)

        # --- Панель горячих клавиш внизу ---
        hotkey_bar = tk.Frame(self.root_frame, pady=5, padx=12)
        self.accent_frames.append(hotkey_bar)
        hotkey_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.hotkey_labels = []
        for key, lang_key in [("F5","scan_btn"),("Ctrl+F","search_hint"),("Esc","clear_btn"),("⌫","back_btn")]:
            k = tk.Label(hotkey_bar, text=f" {key} ", font=("Consolas", 9, "bold"), relief="solid", bd=1, padx=4, pady=1)
            k.pack(side=tk.LEFT, padx=(0, 3))
            d = tk.Label(hotkey_bar, font=("Segoe UI", 9), padx=2)
            d.pack(side=tk.LEFT, padx=(0, 16))
            self.hotkey_labels.append((k, d, lang_key))

    def on_tree_hover(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.cancel_hover_preview()
            return

        if self.hovered_item != item_id:
            self.cancel_hover_preview()
            self.hovered_item = item_id
            self.hover_timer = self.root.after(600, lambda: self.show_hover_preview(event, item_id))

    def show_hover_preview(self, event, item_id):
        values = self.tree.item(item_id, "values")
        if not values or not values[0]: return  
        
        f_path = values[0]
        full_path = os.path.join(self.sub_path.get(), f_path)
        img_pil, _ = self.get_cached_image(full_path, (300, 300))
        
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.wm_overrideredirect(True)
        self.preview_window.attributes("-topmost", True)
        
        thm = THEMES[self.current_theme]
        frame = tk.Frame(self.preview_window, bg=thm["accent"], bd=2, relief="solid")
        frame.pack(fill=tk.BOTH, expand=True)
        
        if not img_pil:
            missing_text = LANG.get(self.current_lang, LANG["EN"]).get("img_missing", "IMAGE MISSING")
            lbl = tk.Label(frame, text=missing_text, bg=thm["panel_bg"], fg=thm["fail_fg"], font=("Segoe UI", 12, "bold"), padx=20, pady=20)
            lbl.pack()
        else:
            # Создаем PhotoImage в главном потоке
            tk_img = ImageTk.PhotoImage(img_pil)
            lbl = tk.Label(frame, image=tk_img, bg=thm["panel_bg"])
            lbl.image = tk_img 
            lbl.pack(padx=2, pady=2)

        x = self.root.winfo_pointerx() + 15
        y = self.root.winfo_pointery() + 15
        # Не даём тултипу выйти за края экрана
        self.preview_window.update_idletasks()
        tw = self.preview_window.winfo_reqwidth()
        th = self.preview_window.winfo_reqheight()
        sw = self.preview_window.winfo_screenwidth()
        sh = self.preview_window.winfo_screenheight()
        if x + tw > sw: x = max(0, sw - tw - 5)
        if y + th > sh: y = max(0, sh - th - 5)
        self.preview_window.geometry(f"+{x}+{y}")

    def cancel_hover_preview(self, event=None):
        if self.hover_timer:
            self.root.after_cancel(self.hover_timer)
            self.hover_timer = None
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
        self.hovered_item = None

    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.save_config()
        self.apply_theme()
        self.populate_treeview()

    def change_lang_event(self, event):
        # Parse "🇷🇺 RU" → "RU"
        selected = self.lang_combo.get()
        self.current_lang = selected.split()[-1]
        self.save_config()
        self.update_ui_lang()
        # Sync combobox display value in case of re-render
        LANG_FLAGS = {
            "RU": "🇷🇺", "EN": "🇬🇧", "JA": "🇯🇵", "KO": "🇰🇷",
            "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸", "PT": "🇵🇹", "CN": "🇨🇳"
        }
        self.lang_combo.set(f"{LANG_FLAGS.get(self.current_lang, '')} {self.current_lang}")

    def update_ui_lang(self):
        l = LANG.get(self.current_lang, LANG["EN"])
        self.root.title(l["title"])
        self.btn_scan.config(text=l["scan_btn"])
        self.btn_theme.config(text=l["theme_btn"])
        self.lbl_base.config(text=l["base_mod"])
        self.lbl_sub.config(text=l["sub_mod"])
        self.lbl_addon.config(text=l["addon_mod"])
        self.radio_sub.config(text=l["mode_sub"])
        self.radio_addon.config(text=l["mode_addon"])
        self.lbl_list.config(text=l["file_label"])
        self.btn_replace.config(text=l["start_replace"])
        self.btn_clear.config(text=l["clear_btn"])
        self.btn_back.config(text=l.get("back_btn", "Back"))
        self.lbl_filename.config(text=l["select_file"] if not self.current_selected_rel_path else os.path.basename(self.current_selected_rel_path))
        self.orig_canvas.config(text=l["orig_view"])
        self.sub_canvas.config(text=l["sub_view"])
        self.addon_canvas.config(text=l["addon_view"])
        self.sync_navigation_ui()
        self._refresh_mode_ui()
        for k_lbl, d_lbl, lang_key in getattr(self, 'hotkey_labels', []):
            if d_lbl.winfo_exists():
                d_lbl.config(text=l.get(lang_key, ""))

    def sync_navigation_ui(self):
        l = LANG.get(self.current_lang, LANG["EN"])
        all_opt = l["all_folders"]
        options = [all_opt] + self.last_scanned_dirs
        if self.current_nav_path not in options and self.current_nav_path != "gfx":
            options.append(self.current_nav_path)
        self.folder_combo.config(values=options)
        if self.current_nav_path == "gfx":
            self.folder_combo.set(all_opt)
        else:
            self.folder_combo.set(self.current_nav_path)
        nav_text = self.current_nav_path.replace(os.sep, " > ")
        self.lbl_nav.config(text=nav_text)

    def clear_search(self):
        self.search_var.set("")
        self.current_nav_path = "gfx"
        self.sync_navigation_ui()
        self.populate_treeview()

    def go_back(self):
        if os.sep in self.current_nav_path:
            self.current_nav_path = os.path.dirname(self.current_nav_path)
            self.sync_navigation_ui()
            self.populate_treeview()

    def on_combo_select(self, event):
        val = self.folder_var.get()
        l = LANG.get(self.current_lang, LANG["EN"])
        if val == l["all_folders"]:
            self.current_nav_path = "gfx"
        else:
            self.current_nav_path = val
        self.populate_treeview()

    def get_path(self, var):
        p = filedialog.askdirectory()
        if p: var.set(os.path.normpath(p))

    def schedule_search(self):
        if self._search_timer: self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(250, self.populate_treeview)

    def populate_treeview(self):
        self.tree.delete(*self.tree.get_children())
        search = self.search_var.get().lower()
        s_root = self.sub_path.get()
        a_root = self.addon_path.get()
        active_path_prefix = self.current_nav_path

        def file_tag(f_path):
            in_sub = os.path.exists(os.path.join(s_root, f_path)) if s_root else False
            in_addon = os.path.exists(os.path.join(a_root, f_path)) if a_root else False
            if in_addon:
                return "addon"
            if in_sub:
                return "exists"
            return "missing"

        if search:
            nodes = {"": ""}
            for f_path in self.files_data:
                if search in f_path.lower() and f_path.startswith(active_path_prefix):
                    parts = f_path.split(os.sep)
                    curr = ""
                    for i, p in enumerate(parts):
                        parent = curr
                        curr = os.path.join(curr, p) if curr else p
                        if curr not in nodes:
                            is_f = (i == len(parts) - 1)
                            tag = "folder"
                            if is_f:
                                tag = file_tag(f_path)
                            icon = "📄 " if is_f else "📂 "
                            nodes[curr] = self.tree.insert(nodes[parent], "end", text=icon + p, 
                                                           values=(f_path if is_f else "", ""), open=True, tags=(tag,))
        else:
            seen_folders = set()
            for f_path in self.files_data:
                if f_path.startswith(active_path_prefix + os.sep) or f_path == active_path_prefix:
                    rel_to_nav = os.path.relpath(f_path, active_path_prefix)
                    if rel_to_nav == ".": continue
                    parts = rel_to_nav.split(os.sep)
                    name = parts[0]
                    if len(parts) > 1:
                        if name not in seen_folders:
                            full_folder_path = os.path.join(active_path_prefix, name)
                            self.tree.insert("", "end", text="📂 " + name, values=("", full_folder_path), tags=("folder",))
                            seen_folders.add(name)
                    else:
                        tag = file_tag(f_path)
                        self.tree.insert("", "end", text="📄 " + name, values=(f_path, ""), tags=(tag,))

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        values = item["values"]
        # Защита: values может быть пустым или иметь меньше 2 элементов
        if not values or len(values) < 2: return
        f_path, folder_path = values[0], values[1]
        if folder_path:
            self.current_nav_path = folder_path
            self.sync_navigation_ui()
            self.populate_treeview()

    def on_select_file(self, event):
        sel = self.tree.selection()
        if not sel: return
        f_path = self.tree.item(sel[0])["values"][0]
        if not f_path:
            self.btn_replace.config(state=tk.DISABLED)
            return
        
        self.current_selected_rel_path = f_path
        self.lbl_filename.config(text=os.path.basename(f_path))
        self.btn_replace.config(state=tk.NORMAL)
        
        self.load_progress = 0
        self.wave_tick = 0
        self._load_gen += 1          # cancel any running animation loop
        my_gen = self._load_gen
        self._animating_wave = True
        self.animate_wave(my_gen)

        threading.Thread(target=self._bg_load, args=(my_gen,), daemon=True).start()

    def animate_wave(self, my_gen=None):
        # Stale loop from a previous file selection: self-cancel
        if my_gen is None or my_gen != self._load_gen:
            return
        if not self._animating_wave:
            return
        
        self.load_progress += 4  
        self.wave_tick += 0.5
        
        if self.load_progress >= 100:
            # Wait for background thread of THIS generation to finish
            if getattr(self, '_bg_load_ready_gen', -1) != my_gen:
                self.root.after(30, lambda: self.animate_wave(my_gen))
                return
            self._animating_wave = False
            # PhotoImage conversion happens strictly on the main thread
            self.root.after(50, lambda: self.update_view(self._temp_io_pil, self._temp_isub_pil, self._temp_iaddon_pil, self._temp_sz))
            return
            
        thm = THEMES[self.current_theme]
        w, h = 150, 150
        img = Image.new("RGB", (w, h), thm["canvas_bg"])
        draw = ImageDraw.Draw(img)
        
        wave_height = 8
        freq = 0.08
        water_y = h - (h * self.load_progress / 100)
        
        points = [(0, h)]
        for x in range(w):
            y = water_y + math.sin(x * freq + self.wave_tick) * wave_height
            points.append((x, y))
        points.append((w, h))
        
        draw.polygon(points, fill=thm["accent"])
        text = f"{int(self.load_progress)}%"
        
        draw.text((w//2 - 10, h//2 - 10), text, fill=thm["fg"] if self.load_progress < 50 else thm["canvas_bg"])
        
        self._wave_img = ImageTk.PhotoImage(img)
        self.orig_canvas.config(image=self._wave_img, text="")
        self.sub_canvas.config(image=self._wave_img, text="")
        self.addon_canvas.config(image=self._wave_img, text="")
        
        self.root.after(30, lambda: self.animate_wave(my_gen))

    def _bg_load(self, my_gen):
        selected_at_start = self.current_selected_rel_path
        p_orig  = os.path.join(self.base_path.get(), selected_at_start)
        p_sub   = os.path.join(self.sub_path.get(),  selected_at_start)
        p_addon = os.path.join(self.addon_path.get(), selected_at_start) if self.addon_path.get() else ""
        io_pil,    sz = self.get_cached_image(p_orig,  (400, 400))
        isub_pil,   _ = self.get_cached_image(p_sub,   (400, 400))
        iaddon_pil, _ = self.get_cached_image(p_addon, (400, 400)) if p_addon else (None, None)
        # If user switched file while loading, discard silently
        if selected_at_start != self.current_selected_rel_path: return
        if my_gen != self._load_gen: return
        self._temp_io_pil     = io_pil
        self._temp_isub_pil   = isub_pil
        self._temp_iaddon_pil = iaddon_pil
        self._temp_sz         = sz
        self._bg_load_ready_gen = my_gen  # Signal ready for this generation

    def get_cached_image(self, path, max_size):
        if not os.path.exists(path): return None, None
        mtime = os.path.getmtime(path)
        with self._cache_lock:
            if path in self.image_cache:
                cached_mtime, img_pil, sz = self.image_cache[path]
                if cached_mtime == mtime: return img_pil, sz
        try:
            with Image.open(path) as img:
                img.load()
                w, h  = img.size
                thumb = img.copy()
                thumb.thumbnail(max_size, Image.Resampling.LANCZOS)
                with self._cache_lock:
                    if len(self.image_cache) >= 200:
                        del self.image_cache[next(iter(self.image_cache))]
                    self.image_cache[path] = (mtime, thumb, f"{w}x{h}")
                return thumb, f"{w}x{h}"
        except Exception:
            return None, None

    def update_view(self, io_pil, isub_pil, iaddon_pil, sz):
        # Исправлено: конвертация в PhotoImage происходит строго в главном потоке!
        if io_pil:
            self.tk_cache['orig'] = ImageTk.PhotoImage(io_pil)
            self.orig_canvas.config(image=self.tk_cache['orig'], text="")
        else:
            self.orig_canvas.config(image="", text=LANG[self.current_lang]["not_found"])

        if isub_pil:
            self.tk_cache['sub'] = ImageTk.PhotoImage(isub_pil)
            self.sub_canvas.config(image=self.tk_cache['sub'], text="")
        else:
            self.sub_canvas.config(image="", text=LANG[self.current_lang]["not_found"])

        if iaddon_pil:
            self.tk_cache['addon'] = ImageTk.PhotoImage(iaddon_pil)
            self.addon_canvas.config(image=self.tk_cache['addon'], text="")
        else:
            self.addon_canvas.config(image="", text=LANG[self.current_lang]["addon_view"])

        self.lbl_size.config(text=f"{LANG[self.current_lang]['size_lbl']} {sz}" if sz else "")

    def open_image_editor(self):
        if not self.current_selected_rel_path: return
        l = LANG.get(self.current_lang, LANG["EN"])

        # Определяем куда писать
        if self.write_mode.get() == "addon":
            if not self.addon_path.get():
                messagebox.showerror("Error", l.get("err_addon", "Select addon folder first!"))
                return
            dest = os.path.join(self.addon_path.get(), self.current_selected_rel_path)
        else:
            if not self.sub_path.get():
                messagebox.showerror("Error", l.get("err_dir", "Select sub-mod folder first!"))
                return
            dest = os.path.join(self.sub_path.get(), self.current_selected_rel_path)

        src = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.dds *.tga")])
        if not src: return
        
        base_img = os.path.join(self.base_path.get(), self.current_selected_rel_path)
        
        editor = ImageEditorPro(self.root, src, dest, base_img, l, THEMES[self.current_theme], self.on_editor_success)
        editor.grab_set()

    def on_editor_success(self):
        sub_dest   = os.path.join(self.sub_path.get(), self.current_selected_rel_path)
        addon_dest = os.path.join(self.addon_path.get(), self.current_selected_rel_path) if self.addon_path.get() else ""
        with self._cache_lock:
            for path in [sub_dest, addon_dest]:
                if path and path in self.image_cache:
                    del self.image_cache[path]
        self.populate_treeview()

        # Диалог показываем ДО запуска анимации — иначе он блокирует Tk
        # и анимация не играет пока пользователь не нажмёт OK.
        messagebox.showinfo(LANG[self.current_lang]["success_title"],
                            LANG[self.current_lang]["success_msg"])

        self.load_progress = 0
        self.wave_tick = 0
        self._load_gen += 1
        my_gen = self._load_gen
        self._animating_wave = True
        self.animate_wave(my_gen)
        threading.Thread(target=self._bg_load, args=(my_gen,), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = HOI4ModdingStudio(root)
    root.mainloop()