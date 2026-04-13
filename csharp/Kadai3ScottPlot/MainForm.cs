using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using ScottPlot;
using ScottPlot.WinForms;

namespace Kadai3ScottPlot;

public sealed class MainForm : Form
{
    private const double StepX = 0.1;
    private const int TimerIntervalMs = 100;
    private const double InitialAxisMaxX = 10.0;

    private readonly FormsPlot _formsPlot;
    private readonly Timer _timer;
    private readonly Label _currentValueLabel;
    private readonly Button _startButton;
    private readonly Button _stopButton;
    private readonly Button _resetButton;

    private readonly List<double> _xValues = new();
    private readonly List<double> _sinValues = new();
    private readonly List<double> _cosValues = new();

    private double _currentX;

    public MainForm()
    {
        Text = "課題3 Windows Programing + ScottPlot";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(960, 640);
        ClientSize = new Size(1100, 700);

        var topPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Top,
            Height = 56,
            FlowDirection = FlowDirection.LeftToRight,
            Padding = new Padding(12, 10, 12, 10),
            BackColor = Color.FromArgb(245, 245, 245),
        };

        _startButton = new Button
        {
            Text = "開始",
            Width = 100,
            Height = 32,
        };
        _startButton.Click += (_, _) => _timer.Start();

        _stopButton = new Button
        {
            Text = "停止",
            Width = 100,
            Height = 32,
        };
        _stopButton.Click += (_, _) => _timer.Stop();

        _resetButton = new Button
        {
            Text = "リセット",
            Width = 100,
            Height = 32,
        };
        _resetButton.Click += (_, _) => ResetAndRender();

        var descriptionLabel = new Label
        {
            AutoSize = true,
            Text = "タイマーで x を 0.1 ずつ増やし、sin(x) / cos(x) を定期描画します。",
            Margin = new Padding(20, 8, 0, 0),
        };

        topPanel.Controls.Add(_startButton);
        topPanel.Controls.Add(_stopButton);
        topPanel.Controls.Add(_resetButton);
        topPanel.Controls.Add(descriptionLabel);

        var plotHost = new Panel
        {
            Dock = DockStyle.Fill,
            Padding = new Padding(18, 12, 18, 18),
            BackColor = Color.White,
        };

        _formsPlot = new FormsPlot
        {
            Dock = DockStyle.Fill,
        };

        _currentValueLabel = new Label
        {
            AutoSize = false,
            Width = 86,
            Height = 34,
            TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI", 11, FontStyle.Bold),
            BackColor = Color.FromArgb(35, 182, 63),
            ForeColor = Color.White,
            Anchor = AnchorStyles.Right | AnchorStyles.Bottom,
        };

        plotHost.Controls.Add(_formsPlot);
        plotHost.Controls.Add(_currentValueLabel);
        plotHost.Resize += (_, _) => PositionCurrentValueLabel();

        Controls.Add(plotHost);
        Controls.Add(topPanel);

        _timer = new Timer
        {
            Interval = TimerIntervalMs,
        };
        _timer.Tick += (_, _) => AdvancePlot();

        ConfigurePlot();
        ResetAndRender();
        _timer.Start();
    }

    private void ConfigurePlot()
    {
        _formsPlot.Plot.Title("Timer + ScottPlot Sample");
        _formsPlot.Plot.Axes.Bottom.Label.Text = "X";
        _formsPlot.Plot.Axes.Left.Label.Text = "Y";
        _formsPlot.Plot.Axes.Right.IsVisible = false;
        _formsPlot.Plot.Axes.Top.IsVisible = false;
        _formsPlot.Plot.Grid.MajorLineColor = Colors.Gray.WithAlpha(0.20);
        _formsPlot.Plot.Grid.MinorLineColor = Colors.Gray.WithAlpha(0.08);
        _formsPlot.Interaction.Enable();
    }

    private void ResetAndRender()
    {
        _timer.Stop();

        _currentX = 0;
        _xValues.Clear();
        _sinValues.Clear();
        _cosValues.Clear();
        AppendCurrentPoint();

        RenderPlot();
    }

    private void AdvancePlot()
    {
        _currentX += StepX;
        AppendCurrentPoint();

        RenderPlot();
    }

    private void AppendCurrentPoint()
    {
        _xValues.Add(_currentX);
        _sinValues.Add(Math.Sin(_currentX));
        _cosValues.Add(Math.Cos(_currentX));
    }

    private void RenderPlot()
    {
        _formsPlot.Plot.Clear();

        if (_xValues.Count > 0)
        {
            var xs = _xValues.ToArray();
            var sinYs = _sinValues.ToArray();
            var cosYs = _cosValues.ToArray();

            var sinScatter = _formsPlot.Plot.Add.Scatter(xs, sinYs);
            sinScatter.LegendText = "sin(x)";
            sinScatter.LineWidth = 2;
            sinScatter.Color = Colors.DodgerBlue;

            var cosScatter = _formsPlot.Plot.Add.Scatter(xs, cosYs);
            cosScatter.LegendText = "cos(x)";
            cosScatter.LineWidth = 2;
            cosScatter.Color = Colors.Orange;

            var cursor = _formsPlot.Plot.Add.VerticalLine(_currentX, 2, Colors.LimeGreen);
            cursor.LinePattern = LinePattern.Solid;
        }

        double maxX = Math.Max(InitialAxisMaxX, Math.Ceiling(_currentX + 1));
        _formsPlot.Plot.Axes.SetLimits(0, maxX, -1.15, 1.15);
        _formsPlot.Plot.ShowLegend(Alignment.UpperRight);
        _formsPlot.Refresh();

        _currentValueLabel.Text = $"{_currentX:F1}";
        PositionCurrentValueLabel();
    }

    private void PositionCurrentValueLabel()
    {
        Control parent = _currentValueLabel.Parent ?? this;
        _currentValueLabel.Left = parent.ClientSize.Width - _currentValueLabel.Width - 22;
        _currentValueLabel.Top = parent.ClientSize.Height - _currentValueLabel.Height - 16;
        _currentValueLabel.BringToFront();
    }
}
