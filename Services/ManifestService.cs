using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

class ManifestService(HttpClient http)
{
    public Task<PatchManifest?> FetchCombinedManifestAsync(string branchValue, CancellationToken ct)
    {
        var branch = BranchExtensions.FromValue(branchValue);
        var config = new LauncherConfig { Branch = branch, DownloadGraphicBundles = false };
        return FetchCombinedManifestAsync(config, ct);
    }

    public async Task<PatchManifest?> FetchCombinedManifestAsync(LauncherConfig config, CancellationToken ct)
    {
        var branchValue = config.Branch.ToValue();
        if (config.Branch == Branch.None) return null;

        var textTask = FetchTextManifestAsync(branchValue, ct);
        Task<PatchManifest?>? r2Task = null;

        if (config.DownloadGraphicBundles)
        {
            var r2Base = Constants.GetR2BaseUrl(config.Branch);
            if (!string.IsNullOrEmpty(r2Base))
            {
                r2Task = FetchR2BundleManifestAsync(r2Base, ct);
            }
        }

        PatchManifest? textManifest = null;
        PatchManifest? bundleManifest = null;

        try { textManifest = await textTask; } catch { }
        if (r2Task != null)
        {
            try { bundleManifest = await r2Task; } catch { }
        }

        if (textManifest is null && bundleManifest is null)
            return null;

        return MergeManifests(textManifest, bundleManifest);
    }

    public async Task<PatchManifest?> FetchTextManifestAsync(string branchValue, CancellationToken ct)
    {
        var url = $"https://raw.githubusercontent.com/{Constants.Repo}/refs/heads/{branchValue}/PatchManifest.json";
        try
        {
            using var response = await http.GetAsync(url, ct);
            if (!response.IsSuccessStatusCode) return null;
            var json = await response.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize(json, AppJsonContext.Default.PatchManifest);
        }
        catch { return null; }
    }

    public async Task<PatchManifest?> FetchR2BundleManifestAsync(string r2BaseUrl, CancellationToken ct)
    {
        var url = $"{r2BaseUrl.TrimEnd('/')}/BundleManifest.json";
        try
        {
            using var response = await http.GetAsync(url, ct);
            if (!response.IsSuccessStatusCode) return null;
            var json = await response.Content.ReadAsStringAsync(ct);
            var manifest = JsonSerializer.Deserialize(json, AppJsonContext.Default.PatchManifest);
            if (manifest?.Files != null)
            {
                foreach (var file in manifest.Files)
                {
                    if (string.IsNullOrEmpty(file.DownloadUrl))
                    {
                        var baseUrl = !string.IsNullOrEmpty(file.OriginalDownloadUrl) ? file.OriginalDownloadUrl : r2BaseUrl;
                        file.DownloadUrl = $"{baseUrl.TrimEnd('/')}/{file.FinalizedFileName}";
                    }
                }
            }
            return manifest;
        }
        catch { return null; }
    }

    public static PatchManifest MergeManifests(PatchManifest? textManifest, PatchManifest? bundleManifest)
    {
        if (textManifest is null) return bundleManifest!;
        if (bundleManifest is null) return textManifest;

        var combined = new PatchManifest
        {
            UpdateDate = bundleManifest.UpdateDate ?? textManifest.UpdateDate,
            StringVersion = !string.IsNullOrWhiteSpace(bundleManifest.StringVersion)
                ? $"{textManifest.StringVersion} | R2:{bundleManifest.StringVersion}"
                : textManifest.StringVersion,
            PatchNote = CombineNotes(textManifest.PatchNote, bundleManifest.PatchNote),
            Files = []
        };

        var fileMap = new Dictionary<string, PatchFileInfo>(StringComparer.OrdinalIgnoreCase);

        foreach (var file in textManifest.Files)
        {
            var key = $"{file.FolderPath.Replace('\\', '/')}/{file.FinalizedFileName}";
            fileMap[key] = file;
        }

        foreach (var file in bundleManifest.Files)
        {
            var key = $"{file.FolderPath.Replace('\\', '/')}/{file.FinalizedFileName}";
            fileMap[key] = file;
        }

        combined.Files = fileMap.Values.ToList();
        return combined;
    }

    private static string? CombineNotes(string? textNotes, string? bundleNotes)
    {
        var parts = new List<string>();
        if (!string.IsNullOrWhiteSpace(textNotes))
            parts.Add(textNotes.Trim());
        if (!string.IsNullOrWhiteSpace(bundleNotes))
            parts.Add($"Image Patch:\n{bundleNotes.Trim()}");
        return parts.Count > 0 ? string.Join("\n\n", parts) : null;
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

        var installedByKey = new Dictionary<string, PatchFileInfo>(StringComparer.OrdinalIgnoreCase);
        foreach (var f in installed.Files)
            installedByKey[$"{f.FolderPath.Replace('\\', '/')}/{f.FinalizedFileName}"] = f;

        foreach (var asset in remote.Files)
        {
            if (string.IsNullOrEmpty(config.GamePath)) return new("Please set Game Folder first!", "Orange");

            var fullPath = Path.Combine(config.GamePath, asset.FolderPath, asset.FinalizedFileName);
            if (!File.Exists(fullPath))
                return new($"Missing file: {asset.OriginalFileName}", "Orange");

            var key = $"{asset.FolderPath.Replace('\\', '/')}/{asset.FinalizedFileName}";
            if (!installedByKey.TryGetValue(key, out var old) || old.Hash != asset.Hash)
                return new($"Update required for {asset.OriginalFileName}", "Orange");
        }

        return new("Everything up to date!", "Green");
    }
}
