using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Windows.Forms;
using ScottPlot.WinForms;
using DrawingColor = System.Drawing.Color;
using DrawingFont = System.Drawing.Font;
using DrawingFontStyle = System.Drawing.FontStyle;
using DrawingSize = System.Drawing.Size;
using FormsLabel = System.Windows.Forms.Label;
using FormsTimer = System.Windows.Forms.Timer;
using ThreadingTimer = System.Threading.Timer;
using TimersTimer = System.Timers.Timer;

namespace Kadai3ScottPlot;

public sealed class TimerComparisonForm : Form
{
    private const double InitialAxisMaxX = 10.0;

    private readonly ComparisonPane _winFormsPane;
    private readonly ComparisonPane _threadingPane;
    private readonly ComparisonPane _timersPane;

    private readonly Func<double, double> _series1;
    private readonly Func<double, double> _series2;
    private readonly double _minY;
    private readonly double _maxY;
    private readonly bool _splitAtNaN;
    private readonly bool _useFixedYAxis;
    private readonly double _speedMultiplier;
    private readonly int _timerIntervalMs;

    public TimerComparisonForm(
        string modeName,
        Func<double, double> series1,
        Func<double, double> series2,
        double minY,
        double maxY,
        bool splitAtNaN,
        bool useFixedYAxis,
        double speedMultiplier,
        int timerIntervalMs)
    {
        _series1 = series1;
        _series2 = series2;
        _minY = minY;
        _maxY = maxY;
        _splitAtNaN = splitAtNaN;
        _useFixedYAxis = useFixedYAxis;
        _speedMultiplier = speedMultiplier;
        _timerIntervalMs = timerIntervalMs;

        Text = $"Timer比較 - {modeName}";
        StartPosition = FormStartPosition.CenterParent;
        MinimumSize = new DrawingSize(1200, 760);
        ClientSize = new DrawingSize(1380, 820);

        var descriptionLabel = new FormsLabel
        {
            Dock = DockStyle.Top,
            Height = 52,
            Padding = new Padding(12, 12, 12, 8),
            Font = new DrawingFont("Segoe UI", 10, DrawingFontStyle.Regular),
            Text = "同じ関数・同じ速度で 3 種類の Timer を同時に動かしています。更新回数と経過時間を見比べて違いを確認できます。",
        };

        var table = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 3,
            RowCount = 1,
            Padding = new Padding(10),
        };
        table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.333f));
        table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.333f));
        table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 33.333f));

        _winFormsPane = CreatePane("System.Windows.Forms.Timer");
        _threadingPane = CreatePane("System.Threading.Timer");
        _timersPane = CreatePane("System.Timers.Timer");

        table.Controls.Add(_winFormsPane.HostPanel, 0, 0);
        table.Controls.Add(_threadingPane.HostPanel, 1, 0);
        table.Controls.Add(_timersPane.HostPanel, 2, 0);

        Controls.Add(table);
        Controls.Add(descriptionLabel);

        _winFormsPane.FormsTimer = new FormsTimer
        {
            Interval = _timerIntervalMs,
        };
        _winFormsPane.FormsTimer.Tick += (_, _) => AdvancePane(_winFormsPane);

        _threadingPane.ThreadingTimer = new ThreadingTimer(
            _ => OnBackgroundTimerTick(_threadingPane),
            null,
            Timeout.Infinite,
            Timeout.Infinite);

        _timersPane.TimersTimer = new TimersTimer(_timerIntervalMs)
        {
            AutoReset = true,
        };
        _timersPane.TimersTimer.Elapsed += (_, _) => OnBackgroundTimerTick(_timersPane);

        ResetPane(_winFormsPane);
        ResetPane(_threadingPane);
        ResetPane(_timersPane);

        StartTimers();
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        StopTimers();
        _threadingPane.ThreadingTimer?.Dispose();
        _timersPane.TimersTimer?.Dispose();
        base.OnFormClosed(e);
    }

    private ComparisonPane CreatePane(string title)
    {
        var hostPanel = new Panel
        {
            Dock = DockStyle.Fill,
            Padding = new Padding(8),
            Margin = new Padding(6),
            BackColor = DrawingColor.White,
        };

        var titleLabel = new FormsLabel
        {
            Dock = DockStyle.Top,
            Height = 28,
            Font = new DrawingFont("Segoe UI", 11, DrawingFontStyle.Bold),
            Text = title,
        };

        var statusLabel = new FormsLabel
        {
            Dock = DockStyle.Top,
            Height = 40,
            Font = new DrawingFont("Segoe UI", 9, DrawingFontStyle.Regular),
        };

        var plot = new FormsPlot
        {
            Dock = DockStyle.Fill,
        };

        hostPanel.Controls.Add(plot);
        hostPanel.Controls.Add(statusLabel);
        hostPanel.Controls.Add(titleLabel);

        return new ComparisonPane(hostPanel, plot, statusLabel, title);
    }

    private void StartTimers()
    {
        _winFormsPane.Stopwatch.Restart();
        _threadingPane.Stopwatch.Restart();
        _timersPane.Stopwatch.Restart();

        _winFormsPane.FormsTimer?.Start();
        _threadingPane.ThreadingTimer?.Change(_timerIntervalMs, _timerIntervalMs);
        _timersPane.TimersTimer?.Start();
    }

    private void StopTimers()
    {
        _winFormsPane.FormsTimer?.Stop();
        _threadingPane.ThreadingTimer?.Change(Timeout.Infinite, Timeout.Infinite);
        _timersPane.TimersTimer?.Stop();
    }

    private void ResetPane(ComparisonPane pane)
    {
        pane.CurrentX = 0;
        pane.TickCount = 0;
        pane.XValues.Clear();
        pane.Series1Values.Clear();
        pane.Series2Values.Clear();
        pane.XValues.Add(0);
        pane.Series1Values.Add(_series1(0));
        pane.Series2Values.Add(_series2(0));
        RenderPane(pane);
    }

    private void AdvancePane(ComparisonPane pane)
    {
        pane.CurrentX += (_timerIntervalMs / 1000.0) * _speedMultiplier;
        pane.TickCount++;
        pane.XValues.Add(pane.CurrentX);
        pane.Series1Values.Add(_series1(pane.CurrentX));
        pane.Series2Values.Add(_series2(pane.CurrentX));
        RenderPane(pane);
    }

    private void RenderPane(ComparisonPane pane)
    {
        pane.Plot.Plot.Clear();

        if (pane.XValues.Count > 0)
        {
            double[] xs = pane.XValues.ToArray();
            double[] series1Ys = pane.Series1Values.ToArray();
            double[] series2Ys = pane.Series2Values.ToArray();

            AddSeries(pane.Plot, xs, series1Ys, ScottPlot.Colors.DodgerBlue);
            AddSeries(pane.Plot, xs, series2Ys, ScottPlot.Colors.Orange);
            pane.Plot.Plot.Add.VerticalLine(pane.CurrentX, 2, ScottPlot.Colors.LimeGreen);
        }

        double maxX = Math.Max(InitialAxisMaxX, Math.Ceiling(pane.CurrentX + 1));
        (double minY, double maxY) = GetYAxisLimits(pane);
        pane.Plot.Plot.Axes.SetLimits(0, maxX, minY, maxY);
        pane.Plot.Plot.Title(pane.Title);
        pane.Plot.Plot.XLabel("X");
        pane.Plot.Plot.YLabel("Y");
        pane.Plot.Refresh();

        pane.StatusLabel.Text =
            $"ticks: {pane.TickCount}    elapsed: {pane.Stopwatch.Elapsed.TotalSeconds:F1}s    x: {pane.CurrentX:F2}";
    }

    private void AddSeries(FormsPlot plot, double[] xs, double[] ys, ScottPlot.Color color)
    {
        if (_splitAtNaN)
        {
            foreach ((double[] segmentXs, double[] segmentYs) in GetFiniteSegments(xs, ys))
            {
                AddScatterLine(plot, segmentXs, segmentYs, color);
            }

            return;
        }

        AddScatterLine(plot, xs, ys, color);
    }

    private static void AddScatterLine(FormsPlot plot, double[] xs, double[] ys, ScottPlot.Color color)
    {
        if (xs.Length == 0)
        {
            return;
        }

        var scatter = plot.Plot.Add.Scatter(xs, ys);
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

    private (double MinY, double MaxY) GetYAxisLimits(ComparisonPane pane)
    {
        if (_useFixedYAxis)
        {
            return (_minY, _maxY);
        }

        var finiteValues = pane.Series1Values
            .Concat(pane.Series2Values)
            .Where(value => !double.IsNaN(value) && !double.IsInfinity(value))
            .ToArray();

        if (finiteValues.Length == 0)
        {
            return (_minY, _maxY);
        }

        double minY = Math.Min(_minY, finiteValues.Min());
        double maxY = Math.Max(_maxY, finiteValues.Max());
        double range = Math.Max(0.5, maxY - minY);
        double padding = range * 0.08;

        return (minY - padding, maxY + padding);
    }

    private void OnBackgroundTimerTick(ComparisonPane pane)
    {
        if (IsDisposed || !IsHandleCreated)
        {
            return;
        }

        try
        {
            BeginInvoke((MethodInvoker)(() =>
            {
                if (!IsDisposed)
                {
                    AdvancePane(pane);
                }
            }));
        }
        catch (InvalidOperationException)
        {
        }
        catch (ObjectDisposedException)
        {
        }
    }

    private sealed class ComparisonPane
    {
        public ComparisonPane(Panel hostPanel, FormsPlot plot, FormsLabel statusLabel, string title)
        {
            HostPanel = hostPanel;
            Plot = plot;
            StatusLabel = statusLabel;
            Title = title;
        }

        public Panel HostPanel { get; }
        public FormsPlot Plot { get; }
        public FormsLabel StatusLabel { get; }
        public string Title { get; }
        public Stopwatch Stopwatch { get; } = new();
        public List<double> XValues { get; } = new();
        public List<double> Series1Values { get; } = new();
        public List<double> Series2Values { get; } = new();

        public FormsTimer? FormsTimer { get; set; }
        public ThreadingTimer? ThreadingTimer { get; set; }
        public TimersTimer? TimersTimer { get; set; }
        public double CurrentX { get; set; }
        public int TickCount { get; set; }
    }
}
