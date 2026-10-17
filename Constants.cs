using System;
using System.IO;

namespace KeiLauncher;

static class Constants
{
    public const string Version = "2.0.0";
    public const string Repo = "Special-Operation-Decagrammaton/Build-Assets";
    public const string LauncherRepo = "Special-Operation-Decagrammaton/Kei-Launcher";

    public static readonly string ConfigDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Kei-Launcher");

    public static readonly string ConfigPath = Path.Combine(ConfigDir, "Config.json");
    public static readonly string ManifestPath = Path.Combine(ConfigDir, "Manifest.json");
}
