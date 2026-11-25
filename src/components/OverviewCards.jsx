import { useMemo } from "react";
import { useHistoricalData } from "../hooks/useHistoricalData";

/**
 * Summary stat cards for the swell season overview.
 *
 * Shows 4 key numbers at a glance:
 *   1. Peak month (the month with the highest swell probability)
 *   2. Events per season (average across all years)
 *   3. Avg event duration
 *   4. Typical height range
 *
 * Data source: monthly_climatology.csv filtered by "surfable" scenario.
 * Uses the same card styling as BannerCeara for visual consistency.
 */

const SEASON_ORDER = [9, 10, 11, 12, 1, 2, 3, 4, 5];

const OverviewCards = () => {
  const { climatologia, eventos, loading } = useHistoricalData();

  const stats = useMemo(() => {
    // Filter to surfable scenario
    const surfable = climatologia.filter(
      (d) => d.scenario === "surfable" && d.month
    );

    if (surfable.length === 0) return null;

    // 1. Peak month — highest probability
    const sorted = [...surfable].sort((a, b) => b.probability - a.probability);
    const peakMonth = sorted[0];

    // 2. Events per season — sum mean_events_per_year across all months
    const eventsPerSeason = surfable.reduce(
      (sum, d) => sum + (d.mean_events_per_year || 0), 0
    );

    // 3. Avg event duration — from surfable events
    const surfableEvents = eventos.filter((d) => d.scenario === "surfable");
    const avgDuration = surfableEvents.length > 0
      ? surfableEvents.reduce((sum, d) => sum + (d.duration_hours || 0), 0) / surfableEvents.length
      : 0;

    // 4. Typical height range — p25 to p75 of max_height from surfable events
    const heights = surfableEvents
      .map((d) => d.max_height)
      .filter((h) => h > 0)
      .sort((a, b) => a - b);

    let heightRange = { low: 0, high: 0 };
    if (heights.length > 0) {
      const p25idx = Math.floor(heights.length * 0.25);
      const p75idx = Math.floor(heights.length * 0.75);
      heightRange = {
        low: heights[p25idx],
        high: heights[p75idx],
      };
    }

    // 5. Data coverage
    const totalYears = peakMonth?.total_years || 0;

    return {
      peakMonth: peakMonth?.month_label || "—",
      peakProb: peakMonth ? (peakMonth.probability * 100).toFixed(0) : "—",
      eventsPerSeason: eventsPerSeason.toFixed(1),
      avgDuration: avgDuration.toFixed(0),
      heightLow: heightRange.low.toFixed(1),
      heightHigh: heightRange.high.toFixed(1),
      totalYears,
    };
  }, [climatologia, eventos]);

  if (loading || !stats) return null;

  const cards = [
    {
      title: "Peak Month",
      value: stats.peakMonth,
      detail: `${stats.peakProb}% probability`,
      color: "text-red-600",
    },
    {
      title: "Events / Season",
      value: stats.eventsPerSeason,
      detail: "surfable events avg",
      color: "text-cyan-600",
    },
    {
      title: "Avg Duration",
      value: `${stats.avgDuration}h`,
      detail: "per event",
      color: "text-amber-600",
    },
    {
      title: "Height Range",
      value: `${stats.heightLow}–${stats.heightHigh}m`,
      detail: "P25–P75 max Hs",
      color: "text-teal-600",
    },
  ];

  return (
    <section className="max-w-5xl mx-auto px-4 my-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div
            key={card.title}
            className="bg-white/80 backdrop-blur-sm border border-slate-200/60 rounded-2xl shadow-lg shadow-slate-200/50 p-5 text-center"
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              {card.title}
            </p>
            <p className={`text-2xl md:text-3xl font-bold ${card.color}`}>
              {card.value}
            </p>
            <p className="text-xs text-slate-500 mt-1">{card.detail}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-400 mt-3 text-center">
        Based on {stats.totalYears} year(s) of ERA5 data — &quot;surfable&quot; scenario (Tp &ge; 9s, Hs &ge; 0.8m)
      </p>
    </section>
  );
};

export default OverviewCards;
