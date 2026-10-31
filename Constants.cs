using System;
using System.IO;

namespace KeiLauncher;

static class Constants
{
    public const string Version = "2.0.0";
    public const string Repo = "Special-Operation-Decagrammaton/Build-Assets";
    public const string LauncherRepo = "Special-Operation-Decagrammaton/Kei-Launcher";

    public const string R2PublicUrlEn = "https://pub-d61ce0987ae04fc9bc72f55559c40021.r2.dev";
    public const string R2PublicUrlPt = "https://pub-9686e8cc050847cb90980644ce00b48f.r2.dev";

    public static string? GetR2BaseUrl(Models.Branch branch) => branch switch
    {
        Models.Branch.PtBr => R2PublicUrlPt,
        Models.Branch.EnOri or Models.Branch.EnExt => R2PublicUrlEn,
        _ => null
    };

    public static readonly string ConfigDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Kei-Launcher");

    public static readonly string ConfigPath = Path.Combine(ConfigDir, "Config.json");
    public static readonly string ManifestPath = Path.Combine(ConfigDir, "Manifest.json");
}
