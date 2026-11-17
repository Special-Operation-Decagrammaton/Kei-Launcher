using Avalonia.Controls;
using KeiLauncher.Services;

namespace KeiLauncher.Views;

public partial class DisclaimerWindow : Window
{
    public DisclaimerWindow() : this(new LocalizationService())
    {
    }

    internal DisclaimerWindow(LocalizationService loc)
    {
        InitializeComponent();

        Title = loc["disclaimer_title"];
        HeaderLabel.Text = loc["disclaimer_header"];
        MessageLabel.Text = loc["disclaimer_body"];
        ExitBtn.Content = loc["disclaimer_exit"];
        AcceptBtn.Content = loc["disclaimer_accept"];

        AcceptBtn.Click += (_, _) => Close(true);
        ExitBtn.Click += (_, _) => Close(false);
    }
}
