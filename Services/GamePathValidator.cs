using System.IO;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

static class GamePathValidator
{
    public static bool IsValid(string? gamePath)
    {
        if (string.IsNullOrEmpty(gamePath) || !Directory.Exists(gamePath))
            return false;

        return File.Exists(Path.Combine(gamePath, "BlueArchive.exe"))
            && File.Exists(Path.Combine(gamePath, "run.bat"));
    }
}
