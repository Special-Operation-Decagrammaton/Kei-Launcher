using System;
using System.Globalization;
using System.Resources;

namespace KeiLauncher.Services;

class LocalizationService
{
    static readonly ResourceManager ResMgr = new("KeiLauncher.Resources.Strings", typeof(LocalizationService).Assembly);
    string _lang = "en";

    public string CurrentLanguage => _lang;
    public event Action? LanguageChanged;

    public string this[string key]
    {
        get
        {
            try
            {
                var culture = new CultureInfo(_lang);
                return ResMgr.GetString(key, culture) ?? key;
            }
            catch
            {
                return key;
            }
        }
    }

    public void SetLanguage(string code)
    {
        _lang = code is "en" or "pt" ? code : "en";
        LanguageChanged?.Invoke();
    }
}
