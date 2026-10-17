namespace KeiLauncher.State;

enum DownloadPhase
{
    Idle,
    FetchingManifest,
    DownloadingFiles,
    Done
}

record DownloadProgress(
    DownloadPhase Phase,
    string StatusText,
    double TotalProgress = 0.0,
    double FileProgress = 0.0,
    string Color = "Orange"
);
