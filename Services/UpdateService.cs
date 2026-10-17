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
        var remote = await manifestService.FetchCombinedManifestAsync(config.Branch.ToValue(), ct);
        if (remote is null)
            return (null, new("Failed to fetch manifest.", "Red"));

        var result = manifestService.CheckForUpdates(config, installed, remote);
        return (remote, result);
    }

    public async IAsyncEnumerable<DownloadProgress> PerformUpdateAsync(
        LauncherConfig config, PatchManifest remote, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct)
    {
        yield return new(DownloadPhase.FetchingManifest, "Fetching latest manifest...");
        yield return new(DownloadPhase.DownloadingFiles, "Downloading translation files...");

        var stream = DownloadFileListAsync(
            config.GamePath!,
            remote.Files,
            f => $"https://github.com/{Constants.Repo}/releases/download/{config.Branch.ToValue()}/{f.Hash}",
            "Downloading",
            "Update Complete!",
            ct);

        await foreach (var progress in stream)
            yield return progress;
    }

    public async IAsyncEnumerable<DownloadProgress> PerformUninstallAsync(
        LauncherConfig config, PatchManifest installed, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct)
    {
        var files = installed.Files.Where(f => !string.IsNullOrEmpty(f.OriginalDownloadUrl)).ToList();
        var stream = DownloadFileListAsync(
            config.GamePath!,
            files,
            f => $"{f.OriginalDownloadUrl.TrimEnd('/')}/{f.OriginalFileName}",
            "Reverting",
            "Uninstall Complete!",
            ct);

        await foreach (var progress in stream)
            yield return progress;
    }

    async IAsyncEnumerable<DownloadProgress> DownloadFileListAsync(
        string gamePath,
        IReadOnlyList<PatchFileInfo> files,
        Func<PatchFileInfo, string> getUrl,
        string verb,
        string doneMessage,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct)
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

            await foreach (var (readBytes, fileTotal) in DownloadStreamAsync(http, url, tempPath, destPath, ct))
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
        HttpClient http, string url, string tempPath, string destPath, [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken ct)
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

            if (File.Exists(destPath)) File.Delete(destPath);
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
