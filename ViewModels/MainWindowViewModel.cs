using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using KeiLauncher.Models;
using KeiLauncher.Services;
using KeiLauncher.State;

namespace KeiLauncher.ViewModels;

partial class MainWindowViewModel : ViewModelBase
{
    readonly LauncherState _state;
    readonly ConfigRepository _configRepo;
    readonly ManifestService _manifestService;
    readonly UpdateService _updateService;
    readonly LaunchService _launchService;
    readonly LocalizationService _loc;

    readonly List<Bitmap> _backgroundImages = [];
    int _currentBgIndex;
    DispatcherTimer? _bgTimer;

    CancellationTokenSource? _downloadCts;
    bool _isInitializing;

    [ObservableProperty] public partial Bitmap? CurrentBackgroundImage { get; private set; }
    [ObservableProperty] public partial DownloadPhase Phase { get; private set; } = DownloadPhase.Idle;
    [ObservableProperty] public partial string InstalledPatchDate { get; private set; } = "-";
    [ObservableProperty] public partial string InstalledPatchNote { get; private set; } = "";
    [ObservableProperty] public partial string LatestPatchDate { get; private set; } = "-";
    [ObservableProperty] public partial string LatestPatchNote { get; private set; } = "";
    [ObservableProperty] public partial string SelectedBranch { get; set; } = "none";
    [ObservableProperty] public partial string BranchDescription { get; private set; } = "";
    [ObservableProperty] public partial string StatusText { get; private set; } = "";
    [ObservableProperty] public partial string StatusColor { get; private set; } = "White";
    [ObservableProperty] public partial bool StatusVisible { get; private set; }
    [ObservableProperty] public partial double ProgressValue { get; private set; }
    [ObservableProperty] public partial double FileProgressValue { get; private set; }
    [ObservableProperty] public partial bool ProgressVisible { get; private set; }

    public string[] BranchOptions { get; } = BranchExtensions.AllDisplayValues();

    public bool IsIdle => Phase == DownloadPhase.Idle;
    public bool IsDownloading => Phase != DownloadPhase.Idle && Phase != DownloadPhase.Done;
    public bool CanLaunch => Phase == DownloadPhase.Idle && GamePathValidator.IsValid(_state.Config.GamePath);

    public string LaunchButtonText => IsDownloading ? _loc["cancel"] : _loc["launch"];
    public IBrush LaunchButtonColor => IsDownloading
        ? new SolidColorBrush(Color.Parse("#991b1b"))
        : new SolidColorBrush(Color.Parse("#15803d"));
    public IBrush LaunchButtonHoverColor => IsDownloading
        ? new SolidColorBrush(Color.Parse("#b91c1c"))
        : new SolidColorBrush(Color.Parse("#16a34a"));
    public IBrush LaunchButtonBorderColor => IsDownloading
        ? new SolidColorBrush(Color.Parse("#ef4444"))
        : new SolidColorBrush(Color.Parse("#4ade80"));
    public string InstalledPatchLabel => _loc["installed_patch"];
    public string LatestPatchLabel => _loc["latest_patch"];
    public string BranchLabel => _loc["branch"];
    public string BranchHint => _loc["branch_select_hint"];
    public string SetFolderLabel => _loc["set_folder"];
    public string CheckUpdateLabel => _loc["check_update"];
    public string InstallUpdateLabel => _loc["install_update"];
    public string UninstallLabel => _loc["uninstall"];
    public string SettingsLabel => _loc["settings"];
    public string GamePathDisplay => string.IsNullOrEmpty(_state.Config.GamePath) ? "-" : _state.Config.GamePath;

    public event Action? CloseRequested;
    public event Action? OpenSettingsRequested;
    public event Action<string>? FolderDialogRequested;

    public MainWindowViewModel(
        LauncherState state,
        ConfigRepository configRepo,
        ManifestService manifestService,
        UpdateService updateService,
        LaunchService launchService,
        LocalizationService loc)
    {
        _state = state;
        _configRepo = configRepo;
        _manifestService = manifestService;
        _updateService = updateService;
        _launchService = launchService;
        _loc = loc;
        _loc.LanguageChanged += OnLanguageChanged;

        Initialize();
    }

    void Initialize()
    {
        _isInitializing = true;
        try
        {
            _state.Config = _configRepo.Load();
            _state.InstalledManifest = _manifestService.LoadInstalled();

            SelectedBranch = _state.Config.Branch.ToValue();
            _loc.SetLanguage(_state.Config.Language);
            RefreshBranchDescription();
            RefreshInstalledPatchText();

            if (!GamePathValidator.IsValid(_state.Config.GamePath))
                ShowStatus(_loc["set_folder_first"], "Orange", stay: true);

            InitializeBackgroundRotation();
        }
        finally
        {
            _isInitializing = false;
        }

        _ = RunStartupChecksAsync();
    }

    void InitializeBackgroundRotation()
    {
        try
        {
            var bgDir = Path.Combine(AppContext.BaseDirectory, "Assets", "BG");
            if (Directory.Exists(bgDir))
            {
                foreach (var file in Directory.GetFiles(bgDir, "*.*")
                    .Where(f => f.EndsWith(".jpg", StringComparison.OrdinalIgnoreCase) ||
                                f.EndsWith(".png", StringComparison.OrdinalIgnoreCase) ||
                                f.EndsWith(".jpeg", StringComparison.OrdinalIgnoreCase))
                    .OrderBy(f => f))
                {
                    try { _backgroundImages.Add(new Bitmap(file)); } catch { }
                }
            }

            if (_backgroundImages.Count == 0)
            {
                string[] defaults = ["BG_1.jpg", "BG_2.jpg", "BG_3.jpg"];
                foreach (var name in defaults)
                {
                    try
                    {
                        var uri = new Uri($"avares://KeiLauncher/Assets/BG/{name}");
                        if (AssetLoader.Exists(uri))
                            _backgroundImages.Add(new Bitmap(AssetLoader.Open(uri)));
                    }
                    catch { }
                }
            }

            if (_backgroundImages.Count > 0)
            {
                CurrentBackgroundImage = _backgroundImages[0];
                if (_backgroundImages.Count > 1)
                {
                    _bgTimer = new DispatcherTimer { Interval = TimeSpan.FromMinutes(1) };
                    _bgTimer.Tick += (_, _) =>
                    {
                        _currentBgIndex = (_currentBgIndex + 1) % _backgroundImages.Count;
                        CurrentBackgroundImage = _backgroundImages[_currentBgIndex];
                    };
                    _bgTimer.Start();
                }
            }
        }
        catch { }
    }

    async Task RunStartupChecksAsync()
    {
        var patchCheck = CheckUpdatesAsync();
        if (_state.Config.CheckUpdateOnLaunch)
        {
            var launcherCheck = CheckLauncherUpdateAsync();
            await Task.WhenAll(patchCheck, launcherCheck);
        }
        else
        {
            await patchCheck;
        }
    }

    async Task CheckLauncherUpdateAsync()
    {
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var (latestVersion, releaseUrl) = await _updateService.CheckLauncherUpdateAsync(cts.Token);
        if (latestVersion is not null && UpdateService.IsNewerVersion(Constants.Version, latestVersion))
            LauncherUpdateAvailable?.Invoke(latestVersion, releaseUrl ?? "");
    }

    public event Action<string, string>? LauncherUpdateAvailable;

    [RelayCommand]
    void OpenSettings() => OpenSettingsRequested?.Invoke();

    [RelayCommand]
    void SetFolder() => FolderDialogRequested?.Invoke(_state.Config.GamePath ?? "");

    public void ApplySelectedFolder(string path)
    {
        if (!GamePathValidator.IsValid(path))
        {
            ShowStatus(_loc["st_check_fail"], "Red");
            return;
        }
        _state.Config.GamePath = path;
        _configRepo.Save(_state.Config);
        ShowStatus($"Path set: {path}", "Green");
        OnPropertyChanged(nameof(CanLaunch));
        OnPropertyChanged(nameof(GamePathDisplay));
    }

    partial void OnSelectedBranchChanged(string value)
    {
        _state.Config.Branch = BranchExtensions.FromValue(value);
        _configRepo.Save(_state.Config);
        RefreshBranchDescription();
        if (!_isInitializing)
        {
            ShowStatus($"Branch set to {value}", "Green");
            _ = CheckUpdatesAsync();
        }
    }

    [RelayCommand]
    async Task CheckUpdateAsync() => await CheckUpdatesAsync();

    async Task CheckUpdatesAsync()
    {
        if (_state.Config.Branch == Branch.None)
        {
            ShowStatus(_loc["st_select_branch"], "Red");
            return;
        }
        ShowStatus(_loc["st_checking"], "White", stay: true);

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        var (remote, result) = await _updateService.CheckUpdatesAsync(_state.Config, _state.InstalledManifest, cts.Token);

        if (remote is not null)
        {
            _state.RemoteManifest = remote;
            RefreshLatestPatchText();
        }
        ShowStatus(result.Message, result.Color);
    }

    [RelayCommand]
    async Task InstallUpdateAsync()
    {
        if (_state.Config.Branch == Branch.None) { ShowStatus(_loc["st_select_branch"], "Red"); return; }
        if (!GamePathValidator.IsValid(_state.Config.GamePath)) { ShowStatus(_loc["st_set_folder"], "Red"); return; }

        _downloadCts = new CancellationTokenSource();
        SetPhase(DownloadPhase.DownloadingFiles);

        try
        {
            if (_state.RemoteManifest is null)
            {
                ShowStatus(_loc["st_checking"], "White", stay: true);
                var (remote, _) = await _updateService.CheckUpdatesAsync(_state.Config, _state.InstalledManifest, _downloadCts.Token);
                if (remote is null)
                {
                    ShowStatus(_loc["st_fetch_fail"], "Red");
                    return;
                }
                _state.RemoteManifest = remote;
                RefreshLatestPatchText();
            }

            await foreach (var progress in _updateService.PerformUpdateAsync(_state.Config, _state.RemoteManifest, _state.InstalledManifest, _downloadCts.Token))
                ApplyProgress(progress);

            _manifestService.SaveInstalled(_state.RemoteManifest);
            _state.InstalledManifest = _state.RemoteManifest;
            RefreshInstalledPatchText();
        }
        catch (OperationCanceledException)
        {
            ShowStatus(_loc["st_cancelled"], "Orange");
        }
        catch (Exception ex)
        {
            ShowStatus($"{_loc["st_update_fail"]} ({ex.Message})", "Red");
        }
        finally
        {
            SetPhase(DownloadPhase.Idle);
        }
    }

    [RelayCommand]
    async Task UninstallAsync()
    {
        if (!GamePathValidator.IsValid(_state.Config.GamePath)) { ShowStatus(_loc["st_set_folder"], "Red"); return; }
        _state.InstalledManifest ??= _manifestService.LoadInstalled();
        if (_state.InstalledManifest is null) { ShowStatus("No patch installed to uninstall.", "Red"); return; }

        _downloadCts = new CancellationTokenSource();
        SetPhase(DownloadPhase.DownloadingFiles);

        try
        {
            await foreach (var progress in _updateService.PerformUninstallAsync(_state.Config, _state.InstalledManifest, _downloadCts.Token))
                ApplyProgress(progress);

            _manifestService.DeleteInstalled();
            _state.InstalledManifest = null;
            RefreshInstalledPatchText();
        }
        catch (OperationCanceledException)
        {
            ShowStatus(_loc["st_cancelled"], "Orange");
        }
        catch (Exception ex)
        {
            ShowStatus($"{_loc["st_uninstall_fail"]} ({ex.Message})", "Red");
        }
        finally
        {
            SetPhase(DownloadPhase.Idle);
        }
    }

    [RelayCommand]
    async Task LaunchOrCancelAsync()
    {
        if (IsDownloading)
        {
            CancelDownload();
            return;
        }
        await LaunchGameAsync();
    }

    void CancelDownload()
    {
        _downloadCts?.Cancel();
        ShowStatus(_loc["st_cancelling"], "Orange", stay: true);
    }

    async Task LaunchGameAsync()
    {
        if (!GamePathValidator.IsValid(_state.Config.GamePath))
        {
            ShowStatus(_loc["set_folder_first"], "Orange");
            return;
        }

        var result = await Task.Run(() => _launchService.TryLaunch(_state.Config));
        switch (result)
        {
            case LaunchResult.Success:
                if (_state.Config.CloseOnLaunch)
                    CloseRequested?.Invoke();
                break;
            case LaunchResult.UacCancelled:
                ShowStatus("Launch cancelled (UAC).", "Orange");
                break;
            case LaunchResult.GamePathMissing:
            case LaunchResult.RunBatMissing:
                ShowStatus(_loc["st_check_fail"], "Red");
                break;
            default:
                ShowStatus("Launch error.", "Red");
                break;
        }
    }

    void ApplyProgress(DownloadProgress progress)
    {
        StatusText = progress.StatusText;
        StatusColor = progress.Color;
        StatusVisible = true;
        ProgressValue = progress.TotalProgress;
        FileProgressValue = progress.FileProgress;
        ProgressVisible = progress.Phase != DownloadPhase.Done;

        if (progress.Phase == DownloadPhase.Done)
            SetPhase(DownloadPhase.Done);
    }

    void SetPhase(DownloadPhase phase)
    {
        Phase = phase;
        OnPropertyChanged(nameof(IsIdle));
        OnPropertyChanged(nameof(IsDownloading));
        OnPropertyChanged(nameof(CanLaunch));
        OnPropertyChanged(nameof(LaunchButtonText));
        OnPropertyChanged(nameof(LaunchButtonColor));
        OnPropertyChanged(nameof(LaunchButtonHoverColor));
        OnPropertyChanged(nameof(LaunchButtonBorderColor));
        ProgressVisible = phase != DownloadPhase.Idle && phase != DownloadPhase.Done;
        if (!ProgressVisible)
        {
            ProgressValue = 0;
            FileProgressValue = 0;
        }
    }

    void ShowStatus(string text, string color, bool stay = false)
    {
        StatusText = text;
        StatusColor = color;
        StatusVisible = true;
        if (!stay)
        {
            DispatcherTimer.RunOnce(() => { StatusVisible = false; }, TimeSpan.FromSeconds(4));
        }
    }

    void RefreshBranchDescription()
    {
        BranchDescription = _state.Config.Branch switch
        {
            Branch.EnOri => _loc["desc_en_ori"],
            Branch.EnExt => _loc["desc_en_ext"],
            Branch.PtBr => _loc["desc_pt_br"],
            _ => _loc["desc_none"]
        };
    }

    void RefreshInstalledPatchText()
    {
        var m = _state.InstalledManifest;
        InstalledPatchDate = m?.UpdateDate ?? "-";
        InstalledPatchNote = string.IsNullOrWhiteSpace(m?.PatchNote) ? _loc["no_patch_notes"] : m.PatchNote;
    }

    void RefreshLatestPatchText()
    {
        var m = _state.RemoteManifest;
        LatestPatchDate = m?.UpdateDate ?? "-";
        LatestPatchNote = string.IsNullOrWhiteSpace(m?.PatchNote) ? _loc["no_patch_notes"] : m.PatchNote;
    }

    void OnLanguageChanged()
    {
        OnPropertyChanged(nameof(LaunchButtonText));
        OnPropertyChanged(nameof(LaunchButtonColor));
        OnPropertyChanged(nameof(LaunchButtonHoverColor));
        OnPropertyChanged(nameof(LaunchButtonBorderColor));
        OnPropertyChanged(nameof(InstalledPatchLabel));
        OnPropertyChanged(nameof(LatestPatchLabel));
        OnPropertyChanged(nameof(BranchLabel));
        OnPropertyChanged(nameof(BranchHint));
        OnPropertyChanged(nameof(SetFolderLabel));
        OnPropertyChanged(nameof(CheckUpdateLabel));
        OnPropertyChanged(nameof(InstallUpdateLabel));
        OnPropertyChanged(nameof(UninstallLabel));
        OnPropertyChanged(nameof(SettingsLabel));
        OnPropertyChanged(nameof(GamePathDisplay));
        RefreshBranchDescription();
    }
}
