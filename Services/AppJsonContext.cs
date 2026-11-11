using System.Text.Json.Serialization;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

[JsonSourceGenerationOptions(
    WriteIndented = true,
    PropertyNameCaseInsensitive = true)]
[JsonSerializable(typeof(LauncherConfig))]
[JsonSerializable(typeof(PatchManifest))]
[JsonSerializable(typeof(PatchFileInfo))]
[JsonSerializable(typeof(BundleManifest))]
[JsonSerializable(typeof(BundleFileInfo))]
[JsonSerializable(typeof(Branch))]
internal partial class AppJsonContext : JsonSerializerContext
{
}
