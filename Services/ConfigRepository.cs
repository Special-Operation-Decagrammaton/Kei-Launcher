using System.IO;
using System.Text.Json;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

class ConfigRepository
{
    public LauncherConfig Load()
    {
        if (!File.Exists(Constants.ConfigPath))
            return LauncherConfig.Default;

        try
        {
            var json = File.ReadAllText(Constants.ConfigPath);
            return JsonSerializer.Deserialize(json, AppJsonContext.Default.LauncherConfig) ?? LauncherConfig.Default;
        }
        catch
        {
            return LauncherConfig.Default;
        }
    }

    public void Save(LauncherConfig config)
    {
        Directory.CreateDirectory(Constants.ConfigDir);
        File.WriteAllText(Constants.ConfigPath, JsonSerializer.Serialize(config, AppJsonContext.Default.LauncherConfig));
    }
}
