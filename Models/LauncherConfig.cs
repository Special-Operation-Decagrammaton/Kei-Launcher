namespace KeiLauncher.Models;

class LauncherConfig
{
    public string? GamePath { get; set; }
    public string Language { get; set; } = "en";
    public Branch Branch { get; set; } = Branch.None;
    public bool CloseOnLaunch { get; set; } = true;
    public bool CheckUpdateOnLaunch { get; set; } = true;
    public bool DownloadGraphicBundles { get; set; } = false;

    public static LauncherConfig Default => new();
}
