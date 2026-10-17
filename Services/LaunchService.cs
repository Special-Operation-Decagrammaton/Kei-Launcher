using System;
using System.Diagnostics;
using System.IO;
using KeiLauncher.Models;

namespace KeiLauncher.Services;

enum LaunchResult { Success, GamePathMissing, RunBatMissing, UacCancelled, Error }

class LaunchService
{
    public LaunchResult TryLaunch(LauncherConfig config)
    {
        if (!GamePathValidator.IsValid(config.GamePath))
            return LaunchResult.GamePathMissing;

        var batPath = Path.Combine(config.GamePath!, "run.bat");
        if (!File.Exists(batPath))
            return LaunchResult.RunBatMissing;

        try
        {
            var cmd = $"Start-Process '{batPath}' -Verb RunAs -WorkingDirectory '{config.GamePath}'";
            using var process = Process.Start(new ProcessStartInfo("powershell")
            {
                Arguments = $"-Command \"{cmd}\"",
                UseShellExecute = false,
                RedirectStandardError = true,
                CreateNoWindow = true
            })!;

            process.WaitForExit();
            var stderr = process.StandardError.ReadToEnd();

            if (process.ExitCode != 0 && stderr.Contains("canceled", StringComparison.OrdinalIgnoreCase))
                return LaunchResult.UacCancelled;

            return process.ExitCode == 0 ? LaunchResult.Success : LaunchResult.Error;
        }
        catch
        {
            return LaunchResult.Error;
        }
    }
}
