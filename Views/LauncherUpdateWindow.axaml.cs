using System;
using System.Diagnostics;
using Avalonia.Controls;

namespace KeiLauncher.Views;

public partial class LauncherUpdateWindow : Window
{
    readonly string _url;
    readonly Func<System.Threading.Tasks.Task> _onContinue;

    public LauncherUpdateWindow() : this("0.0.0", "", () => System.Threading.Tasks.Task.CompletedTask)
    {
    }

    public LauncherUpdateWindow(string version, string url, Func<System.Threading.Tasks.Task> onContinue)
    {
        InitializeComponent();
        _url = url;
        _onContinue = onContinue;

        MessageLabel.Text = $"New launcher v{version} is available!";
        DownloadBtn.Click += OnDownloadClicked;
        LaterBtn.Click += OnLaterClicked;
    }

    async void OnDownloadClicked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        Process.Start(new ProcessStartInfo(_url) { UseShellExecute = true });
        Close();
        await _onContinue();
    }

    async void OnLaterClicked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        Close();
        await _onContinue();
    }
}
