using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

class ManifestService(HttpClient http)
{
    public async Task<PatchManifest?> FetchCombinedManifestAsync(string branchValue, CancellationToken ct)
    {
        var url = $"https://raw.githubusercontent.com/{Constants.Repo}/refs/heads/{branchValue}/PatchManifest.json";
        try
        {
            var response = await http.GetAsync(url, ct);
            if (!response.IsSuccessStatusCode) return null;
            var json = await response.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize(json, AppJsonContext.Default.PatchManifest);
        }
        catch { return null; }
    }

    public PatchManifest? LoadInstalled()
    {
        if (!File.Exists(Constants.ManifestPath)) return null;
        try
        {
            var json = File.ReadAllText(Constants.ManifestPath);
            return JsonSerializer.Deserialize(json, AppJsonContext.Default.PatchManifest);
        }
        catch { return null; }
    }

    public void SaveInstalled(PatchManifest manifest)
    {
        Directory.CreateDirectory(Constants.ConfigDir);
        File.WriteAllText(Constants.ManifestPath, JsonSerializer.Serialize(manifest, AppJsonContext.Default.PatchManifest));
    }

    public void DeleteInstalled()
    {
        if (File.Exists(Constants.ManifestPath))
            File.Delete(Constants.ManifestPath);
    }

    public UpdateCheckResult CheckForUpdates(LauncherConfig config, PatchManifest? installed, PatchManifest remote)
    {
        if (installed is null)
            return new("No local manifest found. Update required.", "Orange");

        if (installed.StringVersion != remote.StringVersion)
            return new("New version available!", "Orange");

        var installedByKey = new Dictionary<string, PatchFileInfo>();
        foreach (var f in installed.Files)
            installedByKey[$"{f.FolderPath}/{f.FinalizedFileName}"] = f;

        foreach (var asset in remote.Files)
        {
            if (string.IsNullOrEmpty(config.GamePath)) return new("Please set Game Folder first!", "Orange");

            var fullPath = Path.Combine(config.GamePath, asset.FolderPath, asset.FinalizedFileName);
            if (!File.Exists(fullPath))
                return new($"Missing file: {asset.OriginalFileName}", "Orange");

            var key = $"{asset.FolderPath}/{asset.FinalizedFileName}";
            if (!installedByKey.TryGetValue(key, out var old) || old.Hash != asset.Hash)
                return new($"Update required for {asset.OriginalFileName}", "Orange");
        }

        return new("Everything up to date!", "Green");
    }
}
