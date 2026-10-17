using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using KeiLauncher.Models;
using KeiLauncher.Services;
using KeiLauncher.State;

namespace KeiLauncher.ViewModels;

partial class SettingsWindowViewModel : ViewModelBase
{
    readonly LauncherState _state;
    readonly ConfigRepository _config;
    readonly LocalizationService _loc;
    readonly UpdateService _updateService;

    [ObservableProperty] public partial bool CloseOnLaunch { get; set; }
    [ObservableProperty] public partial bool CheckUpdateOnLaunch { get; set; }
    [ObservableProperty] public partial string StatusText { get; private set; } = "";
    [ObservableProperty] public partial string StatusColor { get; private set; } = "White";

    [ObservableProperty] public partial string SelectedLanguageDisplay { get; set; } = "English";

    public string[] LanguageOptions { get; } = ["English", "Português"];
    public string Title => _loc["settings"];
    public string VersionLabel => $"{_loc["version"]}: v{Constants.Version}";
    public string CloseOnLaunchLabel => _loc["close_on_launch"];
    public string CheckUpdateOnLaunchLabel => _loc["check_update_on_launch"];
    public string GithubRepoLabel => _loc["github_repo"];
    public string CheckUpdateLabel => _loc["launcher_check_update"];
    public string LanguageLabel => _loc["language"];

    public SettingsWindowViewModel(LauncherState state, ConfigRepository config, LocalizationService loc, UpdateService updateService)
    {
        _state = state;
        _config = config;
        _loc = loc;
        _updateService = updateService;
        _loc.LanguageChanged += OnLanguageChanged;

        CloseOnLaunch = state.Config.CloseOnLaunch;
        CheckUpdateOnLaunch = state.Config.CheckUpdateOnLaunch;
        SelectedLanguageDisplay = state.Config.Language == "pt" ? "Português" : "English";
    }

    partial void OnSelectedLanguageDisplayChanged(string value)
    {
        var code = value == "Português" ? "pt" : "en";
        if (_state.Config.Language == code) return;
        _state.Config.Language = code;
        _config.Save(_state.Config);
        _loc.SetLanguage(code);
    }

    partial void OnCloseOnLaunchChanged(bool value)
    {
        _state.Config.CloseOnLaunch = value;
        _config.Save(_state.Config);
    }

    partial void OnCheckUpdateOnLaunchChanged(bool value)
    {
        _state.Config.CheckUpdateOnLaunch = value;
        _config.Save(_state.Config);
    }

    [RelayCommand]
    void OpenGithub() =>
        System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(
            $"https://github.com/{Constants.LauncherRepo}") { UseShellExecute = true });

    [RelayCommand]
    async Task CheckLauncherUpdateAsync()
    {
        StatusText = "Checking launcher version...";
        StatusColor = "Yellow";

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var (latestVersion, releaseUrl) = await _updateService.CheckLauncherUpdateAsync(cts.Token);

        if (latestVersion is null)
        {
            StatusText = "Unable to check. Check your connection.";
            StatusColor = "Red";
            return;
        }

        if (UpdateService.IsNewerVersion(Constants.Version, latestVersion))
        {
            StatusText = $"New Launcher v{latestVersion} available!";
            StatusColor = "Cyan";
        }
        else
        {
            StatusText = "Launcher is up to date!";
            StatusColor = "Green";
        }
    }

    void OnLanguageChanged()
    {
        OnPropertyChanged(nameof(Title));
        OnPropertyChanged(nameof(VersionLabel));
        OnPropertyChanged(nameof(CloseOnLaunchLabel));
        OnPropertyChanged(nameof(CheckUpdateOnLaunchLabel));
        OnPropertyChanged(nameof(GithubRepoLabel));
        OnPropertyChanged(nameof(CheckUpdateLabel));
        OnPropertyChanged(nameof(LanguageLabel));
    }
}
