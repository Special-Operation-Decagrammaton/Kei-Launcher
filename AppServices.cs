using System;
using System.Net.Http;
using System.Threading;
using KeiLauncher.Services;
using KeiLauncher.State;
using KeiLauncher.ViewModels;
using KeiLauncher.Views;

namespace KeiLauncher;

static class AppServices
{
    static readonly HttpClient Http = new(new SocketsHttpHandler
    {
        PooledConnectionLifetime = TimeSpan.FromMinutes(15),
        PooledConnectionIdleTimeout = TimeSpan.FromMinutes(2),
        ConnectTimeout = TimeSpan.FromSeconds(15),
        EnableMultipleHttp2Connections = true
    })
    {
        Timeout = Timeout.InfiniteTimeSpan
    };
    static readonly LauncherState State = new();
    static readonly LocalizationService Loc = new();
    static readonly ConfigRepository Config = new();
    static readonly ManifestService Manifest = new(Http);
    static readonly UpdateService Update = new(Http, Manifest);
    static readonly LaunchService Launch = new();

    public static MainWindowViewModel CreateMainWindowViewModel() =>
        new(State, Config, Manifest, Update, Launch, Loc);

    public static SettingsWindow GetSettingsWindow() =>
        new() { DataContext = new SettingsWindowViewModel(State, Config, Loc, Update) };
}
