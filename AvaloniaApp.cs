using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using KeiLauncher.Views;

namespace KeiLauncher;

public partial class AvaloniaApp : Application
{
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.MainWindow = new MainWindow
            {
                DataContext = AppServices.CreateMainWindowViewModel()
            };
        }

        base.OnFrameworkInitializationCompleted();
    }
}
