# Simple interface translation system: (EN/PT) - Default: English.

_STRINGS = {
    # Main Interface:
    "installed_patch":    {"en": "Installed Patch",            "pt": "Patch Instalado"},
    "latest_patch":       {"en": "Latest Patch",               "pt": "Último Patch"},
    "no_patch_notes":     {"en": "No patch notes available.",  "pt": "Nenhuma nota de patch disponível."},
    "branch":             {"en": "Branch",                     "pt": "Branch"},
    "branch_select_hint": {"en": "Select a branch to see details.", "pt": "Selecione uma branch para ver os detalhes."},
    "set_folder":         {"en": "Set Folder Location",        "pt": "Definir Pasta do Jogo"},
    "check_update":       {"en": "Check Update Patch",         "pt": "Verificar Atualização"},
    "install_update":     {"en": "Install / Update Patch",     "pt": "Instalar / Atualizar Patch"},
    "uninstall":          {"en": "Uninstall Patch",            "pt": "Desinstalar Patch"},
    "launch":             {"en": "Launch",                     "pt": "Iniciar"},
    "set_folder_first":   {"en": "Please set Game Folder first!", "pt": "Defina a pasta do jogo primeiro!"},

    # Branch Descriptions:
    "desc_none":   {"en": "No translation branch selected.", "pt": "Nenhuma branch de tradução selecionada."},
    "desc_en_ori": {"en": "Global English translation only.", "pt": "Tradução em inglês (Global)."},
    "desc_en_ext": {"en": "Global English translation with community additions.", "pt": "Tradução em inglês (Global) com adições da comunidade."},
    "desc_pt_br":  {"en": "Portuguese (Brazil) translation.", "pt": "Tradução em Português (Brasil)."},

    # Settings Popup:
    "settings":        {"en": "Settings",              "pt": "Configurações"},
    "version":         {"en": "Version",               "pt": "Versão"},
    "close_on_launch": {"en": "Close Launcher on Game Launch", "pt": "Fechar o launcher ao iniciar o jogo"},
    "download_images":      {"en": "Download Translated Images",    "pt": "Baixar Imagens Traduzidas"},
    "download_images_hint": {"en": "(This may take a while to download)", "pt": "(Isso pode demorar um pouco para baixar)"},
    "github_repo":          {"en": "GitHub Repository",             "pt": "Repositório no GitHub"},
    "launcher_check_update": {"en": "Check Update",    "pt": "Verificar Atualização"},
    "language":        {"en": "Language",              "pt": "Idioma"},


    # Status (update.py)
    "st_select_branch":  {"en": "Select a branch first!", "pt": "Selecione uma branch primeiro!"},
    "st_set_folder":     {"en": "Set folder first!", "pt": "Defina a pasta primeiro!"},
    "st_checking":       {"en": "Checking manifest...", "pt": "Verificando o manifesto..."},
    "st_fetch_fail":     {"en": "Failed to fetch manifest.", "pt": "Falha ao buscar o manifesto."},
    "st_no_updates":     {"en": "No updates found.", "pt": "Nenhuma atualização encontrada."},
    "st_check_fail":     {"en": "Check failed.", "pt": "Falha na verificação."},
    "st_downloading":    {"en": "Downloading files...", "pt": "Baixando arquivos..."},
    "st_update_done":    {"en": "Update Complete!", "pt": "Atualização concluída!"},
    "st_update_fail":    {"en": "Update failed", "pt": "Falha na atualização"},
    "st_uninstall_done": {"en": "Uninstall Complete!", "pt": "Desinstalação concluída!"},
    "st_uninstall_fail": {"en": "Uninstall failed", "pt": "Falha na desinstalação"},
}

# Language code to display name mapping.
LANG_NAMES = {"en": "English", "pt": "Português"}
NAME_TO_CODE = {v: k for k, v in LANG_NAMES.items()}


class _I18N:
    def __init__(self):
        self.lang = "en"

    def set(self, lang: str):
        self.lang = lang if lang in ("en", "pt") else "en"

    def t(self, key: str, **kwargs) -> str:
        entry = _STRINGS.get(key)
        if not entry:
            return key
        text = entry.get(self.lang) or entry.get("en") or key
        try:
            return text.format(**kwargs) if kwargs else text
        except Exception:
            return text


_i18n = _I18N()


def t(key: str, **kwargs) -> str:
    return _i18n.t(key, **kwargs)


def set_language(lang: str) -> None:
    _i18n.set(lang)


def current_language() -> str:
    return _i18n.lang
