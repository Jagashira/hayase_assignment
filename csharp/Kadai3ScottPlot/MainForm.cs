using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Forms;
using ScottPlot.WinForms;
using DrawingContentAlignment = System.Drawing.ContentAlignment;
using DrawingColor = System.Drawing.Color;
using DrawingFont = System.Drawing.Font;
using DrawingFontStyle = System.Drawing.FontStyle;
using DrawingSize = System.Drawing.Size;
using FormsLabel = System.Windows.Forms.Label;
using FormsTimer = System.Windows.Forms.Timer;

namespace Kadai3ScottPlot;

public sealed class MainForm : Form
{
    private const int TimerIntervalMs = 50;
    private const double InitialAxisMaxX = 10.0;

    private readonly FormsPlot _formsPlot;
    private readonly FormsTimer _timer;
    private readonly FormsLabel _currentValueLabel;
    private readonly FormsLabel _speedLabel;
    private readonly Button _startButton;
    private readonly Button _stopButton;
    private readonly Button _resetButton;
    private readonly Button _halfSpeedButton;
    private readonly Button _normalSpeedButton;
    private readonly Button _fastSpeedButton;
    private readonly Button _fasterSpeedButton;
    private readonly ComboBox _modeComboBox;

    private readonly List<double> _xValues = new();
    private readonly List<double> _series1Values = new();
    private readonly List<double> _series2Values = new();
    private readonly PlotMode[] _plotModes =
    {
        new("Sin vs Cos", "sin(x)", "cos(x)", x => Math.Sin(x), x => Math.Cos(x), -1.15, 1.15, false),
        new("Sin vs Sin(2x)", "sin(x)", "sin(2x)", x => Math.Sin(x), x => Math.Sin(2 * x), -1.15, 1.15, false),
        new("Sin vs Damped Sin", "sin(x)", "e^(-0.12x)sin(3x)", x => Math.Sin(x), x => Math.Exp(-0.12 * x) * Math.Sin(3 * x), -1.15, 1.15, false),
        new("Exp vs Exp Decay", "e^(0.12x)", "e^(-0.12x)", x => Math.Exp(0.12 * x), x => Math.Exp(-0.12 * x), 0, 8, false),
        new("Tan vs Sin", "tan(x)", "sin(x)", SafeTan, x => Math.Sin(x), -3.2, 3.2, true),
    };

    private double _currentX;
    private double _speedMultiplier;
    private PlotMode _selectedMode;

    public MainForm()
    {
        Text = "課題3 Windows Programing + ScottPlot";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new DrawingSize(960, 640);
        ClientSize = new DrawingSize(1100, 700);

        var topPanel = new FlowLayoutPanel
        {
            Dock = DockStyle.Top,
            Height = 56,
            FlowDirection = FlowDirection.LeftToRight,
            Padding = new Padding(12, 10, 12, 10),
            BackColor = DrawingColor.FromArgb(245, 245, 245),
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

        _halfSpeedButton = CreateSpeedButton("0.5x", 0.5);
        _normalSpeedButton = CreateSpeedButton("1.0x", 1.0);
        _fastSpeedButton = CreateSpeedButton("1.7x", 1.7);
        _fasterSpeedButton = CreateSpeedButton("3.0x", 3.0);

        _modeComboBox = new ComboBox
        {
            Width = 220,
            DropDownStyle = ComboBoxStyle.DropDownList,
            Margin = new Padding(18, 0, 0, 0),
        };
        _modeComboBox.Items.AddRange(_plotModes.Select(mode => mode.Name).Cast<object>().ToArray());
        _modeComboBox.SelectedIndexChanged += (_, _) =>
        {
            _selectedMode = _plotModes[_modeComboBox.SelectedIndex];
            ConfigurePlot();
            ResetAndRender();
            _timer.Start();
        };

        _speedLabel = new FormsLabel
        {
            AutoSize = true,
            Margin = new Padding(12, 8, 0, 0),
        };

        topPanel.Controls.Add(_startButton);
        topPanel.Controls.Add(_stopButton);
        topPanel.Controls.Add(_resetButton);
        topPanel.Controls.Add(_halfSpeedButton);
        topPanel.Controls.Add(_normalSpeedButton);
        topPanel.Controls.Add(_fastSpeedButton);
        topPanel.Controls.Add(_fasterSpeedButton);
        topPanel.Controls.Add(_speedLabel);
        topPanel.Controls.Add(_modeComboBox);

        var plotHost = new Panel
        {
            Dock = DockStyle.Fill,
            Padding = new Padding(18, 12, 18, 18),
            BackColor = DrawingColor.White,
        };

        _formsPlot = new FormsPlot
        {
            Dock = DockStyle.Fill,
        };

        _currentValueLabel = new FormsLabel
        {
            AutoSize = false,
            Width = 86,
            Height = 34,
            TextAlign = DrawingContentAlignment.MiddleCenter,
            Font = new DrawingFont("Segoe UI", 11, DrawingFontStyle.Bold),
            BackColor = DrawingColor.FromArgb(35, 182, 63),
            ForeColor = DrawingColor.White,
            Anchor = AnchorStyles.Right | AnchorStyles.Bottom,
        };

        plotHost.Controls.Add(_formsPlot);
        plotHost.Controls.Add(_currentValueLabel);
        plotHost.Resize += (_, _) => PositionCurrentValueLabel();

        Controls.Add(plotHost);
        Controls.Add(topPanel);

        _timer = new FormsTimer
        {
            Interval = TimerIntervalMs,
        };
        _timer.Tick += (_, _) => AdvancePlot();

        _speedMultiplier = 1.0;
        _selectedMode = _plotModes[0];
        _modeComboBox.SelectedIndex = 0;
        UpdateSpeedButtons();
        ConfigurePlot();
        ResetAndRender();
        _timer.Start();
    }

    private void ConfigurePlot()
    {
        _formsPlot.Plot.Title(_selectedMode.Name);
        _formsPlot.Plot.XLabel("X");
        _formsPlot.Plot.YLabel("Y");
        _formsPlot.Plot.Axes.Right.IsVisible = false;
        _formsPlot.Plot.Axes.Top.IsVisible = false;
        _formsPlot.Interaction.Enable();
    }

    private void ResetAndRender()
    {
        _timer.Stop();

        _currentX = 0;
        _xValues.Clear();
        _series1Values.Clear();
        _series2Values.Clear();
        AppendCurrentPoint();

        RenderPlot();
    }

    private void AdvancePlot()
    {
        _currentX += (_timer.Interval / 1000.0) * _speedMultiplier;
        AppendCurrentPoint();

        RenderPlot();
    }

    private void AppendCurrentPoint()
    {
        _xValues.Add(_currentX);
        _series1Values.Add(_selectedMode.Series1(_currentX));
        _series2Values.Add(_selectedMode.Series2(_currentX));
    }

    private void RenderPlot()
    {
        _formsPlot.Plot.Clear();

        if (_xValues.Count > 0)
        {
            var xs = _xValues.ToArray();
            var series1Ys = _series1Values.ToArray();
            var series2Ys = _series2Values.ToArray();

            AddSeries(xs, series1Ys, ScottPlot.Colors.DodgerBlue);
            AddSeries(xs, series2Ys, ScottPlot.Colors.Orange);

            var cursor = _formsPlot.Plot.Add.VerticalLine(_currentX, 2, ScottPlot.Colors.LimeGreen);
            cursor.LinePattern = ScottPlot.LinePattern.Solid;
        }

        double maxX = Math.Max(InitialAxisMaxX, Math.Ceiling(_currentX + 1));
        (double minY, double maxY) = GetYAxisLimits();
        _formsPlot.Plot.Axes.SetLimits(0, maxX, minY, maxY);
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

    private void AddSeries(double[] xs, double[] ys, ScottPlot.Color color)
    {
        if (_selectedMode.SplitAtNaN)
        {
            foreach ((double[] segmentXs, double[] segmentYs) in GetFiniteSegments(xs, ys))
            {
                AddScatterLine(segmentXs, segmentYs, color);
            }

            return;
        }

        AddScatterLine(xs, ys, color);
    }

    private void AddScatterLine(double[] xs, double[] ys, ScottPlot.Color color)
    {
        if (xs.Length == 0)
        {
            return;
        }

        var scatter = _formsPlot.Plot.Add.Scatter(xs, ys);
        scatter.LineWidth = 2;
        scatter.Color = color;
        scatter.MarkerSize = 0;
    }

    private static IEnumerable<(double[] Xs, double[] Ys)> GetFiniteSegments(double[] xs, double[] ys)
    {
        var segmentXs = new List<double>();
        var segmentYs = new List<double>();

        for (int i = 0; i < xs.Length; i++)
        {
            bool isFinite = !double.IsNaN(ys[i]) && !double.IsInfinity(ys[i]);

            if (isFinite)
            {
                segmentXs.Add(xs[i]);
                segmentYs.Add(ys[i]);
                continue;
            }

            if (segmentXs.Count > 0)
            {
                yield return (segmentXs.ToArray(), segmentYs.ToArray());
                segmentXs.Clear();
                segmentYs.Clear();
            }
        }

        if (segmentXs.Count > 0)
        {
            yield return (segmentXs.ToArray(), segmentYs.ToArray());
        }
    }

    private Button CreateSpeedButton(string text, double speedMultiplier)
    {
        var button = new Button
        {
            Text = text,
            Width = 70,
            Height = 32,
        };
        button.Click += (_, _) =>
        {
            _speedMultiplier = speedMultiplier;
            UpdateSpeedButtons();
        };
        return button;
    }

    private void UpdateSpeedButtons()
    {
        UpdateSpeedButtonStyle(_halfSpeedButton, 0.5);
        UpdateSpeedButtonStyle(_normalSpeedButton, 1.0);
        UpdateSpeedButtonStyle(_fastSpeedButton, 1.7);
        UpdateSpeedButtonStyle(_fasterSpeedButton, 3.0);
        _speedLabel.Text = $"速度: {_speedMultiplier:0.0}x";
    }

    private void UpdateSpeedButtonStyle(Button button, double speedMultiplier)
    {
        bool isActive = Math.Abs(_speedMultiplier - speedMultiplier) < 0.001;
        button.BackColor = isActive ? DrawingColor.FromArgb(220, 240, 255) : SystemColors.Control;
    }

    private (double MinY, double MaxY) GetYAxisLimits()
    {
        var finiteValues = _series1Values
            .Concat(_series2Values)
            .Where(value => !double.IsNaN(value) && !double.IsInfinity(value))
            .ToArray();

        if (finiteValues.Length == 0)
        {
            return (_selectedMode.MinY, _selectedMode.MaxY);
        }

        double minY = Math.Min(_selectedMode.MinY, finiteValues.Min());
        double maxY = Math.Max(_selectedMode.MaxY, finiteValues.Max());
        double range = Math.Max(0.5, maxY - minY);
        double padding = range * 0.08;

        return (minY - padding, maxY + padding);
    }

    private static double SafeTan(double x)
    {
        double shifted = x - (Math.PI / 2);
        double distanceFromAsymptote = Math.Abs(shifted - (Math.Round(shifted / Math.PI) * Math.PI));

        if (distanceFromAsymptote <= 0.01)
        {
            return double.NaN;
        }

        return Math.Tan(x);
    }

    private sealed record PlotMode(
        string Name,
        string Series1Name,
        string Series2Name,
        Func<double, double> Series1,
        Func<double, double> Series2,
        double MinY,
        double MaxY,
        bool SplitAtNaN);
}
