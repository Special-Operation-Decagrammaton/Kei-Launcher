using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Platform.Storage;
using KeiLauncher.ViewModels;

namespace KeiLauncher.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    protected override void OnDataContextChanged(System.EventArgs e)
    {
        base.OnDataContextChanged(e);
        if (DataContext is MainWindowViewModel vm)
        {
            vm.FolderDialogRequested += OnFolderDialogRequested;
            vm.OpenSettingsRequested += OnOpenSettingsRequested;
            vm.LauncherUpdateAvailable += OnLauncherUpdateAvailable;
            vm.CloseRequested += Close;
        }
    }

    async void OnFolderDialogRequested(string startPath)
    {
        var options = new FolderPickerOpenOptions
        {
            Title = "Select BlueArchive_JP Folder",
            AllowMultiple = false
        };
        var result = await StorageProvider.OpenFolderPickerAsync(options);
        if (result.Count > 0 && DataContext is MainWindowViewModel vm)
            vm.ApplySelectedFolder(result[0].TryGetLocalPath() ?? "");
    }

    void OnOpenSettingsRequested()
    {
        if (DataContext is not MainWindowViewModel vm) return;
        var win = AppServices.GetSettingsWindow();
        win.ShowDialog(this);
    }

    void OnLauncherUpdateAvailable(string version, string url)
    {
        var win = new LauncherUpdateWindow(version, url, onContinue: async () =>
        {
            if (DataContext is MainWindowViewModel vm)
                await vm.CheckUpdateCommand.ExecuteAsync(null);
        });
        win.ShowDialog(this);
    }
}