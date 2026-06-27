# Simple interface translation system (en/pt). default: English
# Nonexistent key falls back into itself (degrades without breaking).

_STRINGS = {
    #Main Interface (persistent)          
    "installed_patch":    {"en": "Installed Patch",            "pt": "Patch Instalado"},
    "latest_patch":       {"en": "Latest Patch",               "pt": "Último Patch"},
    "no_patch_notes":     {"en": "No patch notes available.",  "pt": "Nenhuma nota de patch disponível."},
    "branch":             {"en": "Branch",                     "pt": "Branch"},
    "branch_select_hint": {"en": "Select a branch to see details.", "pt": "Selecione uma branch para ver os detalhes."},
    "set_folder":         {"en": "Set Folder Location",        "pt": "Definir Pasta do Jogo"},
    "check_update":       {"en": "Check Update Patch",         "pt": "Verificar Atualização"},
    "install_update":     {"en": "Install / Update Patch",     "pt": "Instalar / Atualizar Patch"},
    "uninstall":          {"en": "Uninstall Patch",            "pt": "Desinstalar Patch"},
    "deploy_android":     {"en": "Deploy to Android",          "pt": "Instalar no Android"},
    "launch":             {"en": "Launch",                     "pt": "Iniciar"},
    "set_folder_first":   {"en": "Please set Game Folder first!", "pt": "Defina a pasta do jogo primeiro!"},

    #Branch descriptions   
    "desc_none":   {"en": "No translation branch selected.", "pt": "Nenhuma branch de tradução selecionada."},
    "desc_en_ori": {"en": "Global English translation only.", "pt": "Tradução em inglês (Global)."},
    "desc_en_ext": {"en": "Global English translation with community additions.", "pt": "Tradução em inglês (Global) com adições da comunidade."},
    "desc_pt_br":  {"en": "Português (Brasil) translation.", "pt": "Tradução em Português (Brasil)."},

    # Settings popup
    "settings":        {"en": "Settings",              "pt": "Configurações"},
    "version":         {"en": "Version",               "pt": "Versão"},
    "close_on_launch": {"en": "Close Launcher on Game Launch", "pt": "Fechar o launcher ao iniciar o jogo"},
    "github_repo":     {"en": "GitHub Repository",     "pt": "Repositório no GitHub"},
    "launcher_check_update": {"en": "Check Update",    "pt": "Verificar Atualização"},
    "language":        {"en": "Language",              "pt": "Idioma"},

    # Android deploy
    "android_select_branch": {"en": "Select a translation branch first!", "pt": "Selecione uma branch de tradução primeiro!"},
    "android_confirm_title": {"en": "Deploy to Android", "pt": "Instalar no Android"},
    "android_confirm_body":  {"en": "This overwrites the game's table files on your phone with the '{branch}' translation.\n\nA backup is made first. Modifying game files can risk a ban — use a throwaway account.\n\nContinue?",
                              "pt": "Isto vai sobrescrever os arquivos de tabela do jogo no seu celular com a tradução '{branch}'.\n\nUm backup é feito antes. Modificar arquivos do jogo tem risco de banimento — use uma conta descartável.\n\nContinuar?"},
    "android_yes":     {"en": "Yes, deploy", "pt": "Sim, instalar"},
    "android_cancel":  {"en": "Cancel",      "pt": "Cancelar"},
    "android_checking":   {"en": "Checking phone...",   "pt": "Verificando o celular..."},
    "android_no_adb":     {"en": "adb not found. Install platform-tools or put adb next to the launcher.", "pt": "adb não encontrado. Instale o platform-tools ou coloque o adb junto do launcher."},
    "android_no_device":  {"en": "No Android device. Connect via USB + enable USB debugging.", "pt": "Nenhum dispositivo Android. Conecte via USB e ative a depuração USB."},
    "android_no_gamedir": {"en": "Can't reach the game folder on the phone. Is BA JP installed?", "pt": "Não consegui acessar a pasta do jogo no celular. O BA JP está instalado?"},
    "android_fetching":   {"en": "Fetching manifest...", "pt": "Buscando o manifesto..."},
    "android_no_tables":  {"en": "This branch has no table files to deploy.", "pt": "Esta branch não tem arquivos de tabela para instalar."},
    "android_version_mismatch": {"en": "Phone game version differs from the patch. Update the game/patch first.", "pt": "A versão do jogo no celular é diferente do patch. Atualize o jogo/patch primeiro."},
    "android_downloading": {"en": "Downloading: {n}", "pt": "Baixando: {n}"},
    "android_backing_up":  {"en": "Backing up: {n}",  "pt": "Backup: {n}"},
    "android_pushing":     {"en": "Pushing: {n}",     "pt": "Enviando: {n}"},
    "android_done":        {"en": "Done! Open the game on your phone to check.", "pt": "Pronto! Abra o jogo no celular para conferir."},
    "android_failed":      {"en": "Android deploy failed.", "pt": "Falha ao instalar no Android."},

    #Status (update.py) — keys ready for future use i think
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

# Language code to display name mapping (and vice versa)
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
