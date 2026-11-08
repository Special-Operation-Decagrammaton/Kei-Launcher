using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using KeiLauncher.Models;
using KeiLauncher.State;

namespace KeiLauncher.Services;

class UpdateService(HttpClient http, ManifestService manifestService)
{
    const string UserAgent = "KeiLauncher/2.0";

    public async Task<(PatchManifest? Manifest, UpdateCheckResult Result)> CheckUpdatesAsync(
        LauncherConfig config, PatchManifest? installed, CancellationToken ct)
    {
        var remote = await manifestService.FetchCombinedManifestAsync(config, ct);
        if (remote is null)
            return (null, new("Failed to fetch manifest.", "Red"));

        var result = manifestService.CheckForUpdates(config, installed, remote);
        return (remote, result);
    }

    public async IAsyncEnumerable<DownloadProgress> PerformUpdateAsync(
        LauncherConfig config,
        PatchManifest remote,
        PatchManifest? installed = null,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct = default)
    {
        yield return new(DownloadPhase.FetchingManifest, "Fetching latest manifest...");
        yield return new(DownloadPhase.DownloadingFiles, "Downloading translation and bundle files...");

        var filesToDownload = GetFilesNeedingDownload(config.GamePath!, remote.Files, installed);
        if (filesToDownload.Count == 0)
            filesToDownload = remote.Files;

        var stream = DownloadFileListAsync(
            config.GamePath!,
            filesToDownload,
            f => ResolveDownloadUrl(config, f),
            "Downloading",
            "Update Complete!",
            ct,
            config.BackupBundles);

        await foreach (var progress in stream)
            yield return progress;
    }

    public static List<PatchFileInfo> GetFilesNeedingDownload(
        string gamePath,
        IReadOnlyList<PatchFileInfo> remoteFiles,
        PatchManifest? installed)
    {
        var installedByKey = new Dictionary<string, PatchFileInfo>(StringComparer.OrdinalIgnoreCase);
        if (installed != null)
        {
            foreach (var f in installed.Files)
                installedByKey[$"{f.FolderPath.Replace('\\', '/')}/{f.FinalizedFileName}"] = f;
        }

        var result = new List<PatchFileInfo>();
        foreach (var asset in remoteFiles)
        {
            var fullPath = Path.Combine(gamePath, asset.FolderPath, asset.FinalizedFileName);
            var key = $"{asset.FolderPath.Replace('\\', '/')}/{asset.FinalizedFileName}";

            bool needsDownload = !File.Exists(fullPath) ||
                                !installedByKey.TryGetValue(key, out var old) ||
                                old.Hash != asset.Hash;

            if (needsDownload)
                result.Add(asset);
        }

        return result;
    }

    public static string ResolveDownloadUrl(LauncherConfig config, PatchFileInfo f)
    {
        if (!string.IsNullOrEmpty(f.DownloadUrl))
            return f.DownloadUrl;

        if (!string.IsNullOrEmpty(f.OriginalDownloadUrl) &&
            (f.OriginalDownloadUrl.Contains("r2.dev", StringComparison.OrdinalIgnoreCase) ||
             f.OriginalDownloadUrl.Contains("cloudflarestorage.com", StringComparison.OrdinalIgnoreCase)))
        {
            return $"{f.OriginalDownloadUrl.TrimEnd('/')}/{f.FinalizedFileName}";
        }

        if (f.FinalizedFileName.EndsWith(".bundle", StringComparison.OrdinalIgnoreCase))
        {
            var r2Base = Constants.GetR2BaseUrl(config.Branch);
            if (!string.IsNullOrEmpty(r2Base))
                return $"{r2Base.TrimEnd('/')}/{f.FinalizedFileName}";
        }

        return $"https://github.com/{Constants.Repo}/releases/download/{config.Branch.ToValue()}/{f.Hash}";
    }

    public async IAsyncEnumerable<DownloadProgress> PerformUninstallAsync(
        LauncherConfig config, PatchManifest installed, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct)
    {
        var officialRevertFiles = installed.Files
            .Where(f => !string.IsNullOrEmpty(f.OriginalDownloadUrl) &&
                        (f.OriginalDownloadUrl.Contains("bluearchiveyostar.com", StringComparison.OrdinalIgnoreCase) ||
                         f.OriginalDownloadUrl.Contains("yo-star.com", StringComparison.OrdinalIgnoreCase)))
            .ToList();

        var bundleFiles = installed.Files
            .Where(f => f.FinalizedFileName.EndsWith(".bundle", StringComparison.OrdinalIgnoreCase))
            .ToList();

        if (officialRevertFiles.Count > 0)
        {
            var stream = DownloadFileListAsync(
                config.GamePath!,
                officialRevertFiles,
                f => $"{f.OriginalDownloadUrl.TrimEnd('/')}/{f.OriginalFileName}",
                "Reverting",
                "Revert Complete!",
                ct);

            await foreach (var progress in stream)
            {
                if (bundleFiles.Count > 0 && progress.Phase == DownloadPhase.Done)
                    continue;
                yield return progress;
            }
        }

        int totalBundles = bundleFiles.Count;
        for (int i = 0; i < totalBundles; i++)
        {
            ct.ThrowIfCancellationRequested();
            var b = bundleFiles[i];
            var bPath = Path.Combine(config.GamePath!, b.FolderPath, b.FinalizedFileName);
            var bakPath = bPath + ".bak";

            var name = !string.IsNullOrEmpty(b.OriginalFileName) ? b.OriginalFileName : b.FinalizedFileName;
            yield return new(DownloadPhase.DownloadingFiles, $"Restoring: {name} ({i + 1}/{totalBundles})", (double)(i + 1) / totalBundles, 0.0);

            try
            {
                if (File.Exists(bakPath))
                {
                    if (File.Exists(bPath))
                        File.Delete(bPath);
                    File.Move(bakPath, bPath);
                }
                else if (File.Exists(bPath))
                {
                    File.Delete(bPath);
                }
            }
            catch { }
        }

        yield return new(DownloadPhase.Done, "Uninstall Complete!", 1.0, 1.0, "Green");
    }

    async IAsyncEnumerable<DownloadProgress> DownloadFileListAsync(
        string gamePath,
        IReadOnlyList<PatchFileInfo> files,
        Func<PatchFileInfo, string> getUrl,
        string verb,
        string doneMessage,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct,
        bool backupBundles = false)
    {
        int total = files.Count;
        for (int i = 0; i < total; i++)
        {
            ct.ThrowIfCancellationRequested();
            var asset = files[i];
            var destPath = Path.Combine(gamePath, asset.FolderPath, asset.FinalizedFileName);
            Directory.CreateDirectory(Path.GetDirectoryName(destPath)!);
            var tempPath = destPath + ".tmp";

            var url = getUrl(asset);
            yield return new(DownloadPhase.DownloadingFiles, $"{verb}: {asset.OriginalFileName} ({i + 1}/{total})", (double)i / total, 0.0);

            await foreach (var (readBytes, fileTotal) in DownloadStreamAsync(http, url, tempPath, destPath, ct, backupBundles))
            {
                double fileProgress = fileTotal > 0 ? (double)readBytes / fileTotal : 0.0;
                double overallProgress = (i + fileProgress) / total;
                var sizeInfo = fileTotal > 0
                    ? $" - {FormatSize(readBytes)} / {FormatSize(fileTotal)}"
                    : $" - {FormatSize(readBytes)}";

                yield return new(DownloadPhase.DownloadingFiles, $"{verb}: {asset.OriginalFileName} ({i + 1}/{total}){sizeInfo}", overallProgress, fileProgress);
            }
        }

        yield return new(DownloadPhase.Done, doneMessage, 1.0, 1.0, "Green");
    }

    static async IAsyncEnumerable<(long ReadBytes, long TotalBytes)> DownloadStreamAsync(
        HttpClient http, string url, string tempPath, string destPath, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct, bool backupBundles = false)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, url);
        request.Headers.TryAddWithoutValidation("User-Agent", UserAgent);
        using var response = await http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
        response.EnsureSuccessStatusCode();

        var totalBytes = response.Content.Headers.ContentLength ?? -1L;
        var buffer = new byte[81920];
        long totalRead = 0;
        var lastReport = Stopwatch.GetTimestamp();

        bool succeeded = false;
        try
        {
            await using (var stream = await response.Content.ReadAsStreamAsync(ct))
            await using (var file = new FileStream(tempPath, FileMode.Create, FileAccess.Write, FileShare.None, 81920, useAsync: true))
            {
                int read;
                while ((read = await stream.ReadAsync(buffer.AsMemory(0, buffer.Length), ct)) > 0)
                {
                    await file.WriteAsync(buffer.AsMemory(0, read), ct);
                    totalRead += read;

                    var elapsedMs = Stopwatch.GetElapsedTime(lastReport).TotalMilliseconds;
                    if (elapsedMs >= 50 || (totalBytes > 0 && totalRead == totalBytes))
                    {
                        lastReport = Stopwatch.GetTimestamp();
                        yield return (totalRead, totalBytes);
                    }
                }
            }

            if (File.Exists(destPath))
            {
                if (backupBundles && destPath.EndsWith(".bundle", StringComparison.OrdinalIgnoreCase))
                {
                    var bakPath = destPath + ".bak";
                    if (!File.Exists(bakPath))
                    {
                        try { File.Copy(destPath, bakPath, true); } catch { }
                    }
                }
                File.Delete(destPath);
            }
            File.Move(tempPath, destPath);
            succeeded = true;
        }
        finally
        {
            if (!succeeded && File.Exists(tempPath))
                File.Delete(tempPath);
        }
    }

    static string FormatSize(long bytes)
    {
        if (bytes >= 1024 * 1024 * 1024)
            return $"{bytes / (1024.0 * 1024 * 1024):F1} GB";
        if (bytes >= 1024 * 1024)
            return $"{bytes / (1024.0 * 1024):F1} MB";
        if (bytes >= 1024)
            return $"{bytes / 1024.0:F1} KB";
        return $"{bytes} B";
    }

    public async Task<(string? LatestVersion, string? ReleaseUrl)> CheckLauncherUpdateAsync(CancellationToken ct)
    {
        var url = $"https://api.github.com/repos/{Constants.LauncherRepo}/releases/latest";
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.TryAddWithoutValidation("User-Agent", UserAgent);
            var response = await http.SendAsync(request, ct);
            if (!response.IsSuccessStatusCode) return (null, null);

            using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync(ct));
            var latestVersion = doc.RootElement.GetProperty("tag_name").GetString()?.TrimStart('v');
            var releaseUrl = doc.RootElement.GetProperty("html_url").GetString();
            return (latestVersion, releaseUrl);
        }
        catch { return (null, null); }
    }

    public static bool IsNewerVersion(string current, string latest)
    {
        try
        {
            var curr = current.Split('.').Select(int.Parse).ToArray();
            var late = latest.Split('.').Select(int.Parse).ToArray();
            for (int i = 0; i < Math.Max(curr.Length, late.Length); i++)
            {
                var c = i < curr.Length ? curr[i] : 0;
                var l = i < late.Length ? late[i] : 0;
                if (l > c) return true;
                if (l < c) return false;
            }
            return false;
        }
        catch { return latest != current; }
    }
}
