using CommunityToolkit.Mvvm.ComponentModel;
using KeiLauncher.Models;

namespace KeiLauncher.State;

partial class LauncherState : ObservableObject
{
    [ObservableProperty] public partial LauncherConfig Config { get; set; } = LauncherConfig.Default;
    [ObservableProperty] public partial PatchManifest? InstalledManifest { get; set; }
    [ObservableProperty] public partial PatchManifest? RemoteManifest { get; set; }
}
