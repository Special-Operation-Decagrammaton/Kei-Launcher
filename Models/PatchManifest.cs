using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace KeiLauncher.Models;

class PatchFileInfo
{
    public string OriginalFileName { get; set; } = "";
    public string FinalizedFileName { get; set; } = "";
    public string OriginalDownloadUrl { get; set; } = "";
    public string FolderPath { get; set; } = "";
    [JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
    public long Hash { get; set; }
    public string? DownloadUrl { get; set; }
}

class PatchManifest
{
    public string? PatchNote { get; set; }
    public string? UpdateDate { get; set; }
    public string? StringVersion { get; set; }
    public List<PatchFileInfo> Files { get; set; } = [];
}
