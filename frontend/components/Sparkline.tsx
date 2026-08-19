"use client";

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: boolean;
  className?: string;
}

/**
 * A tiny dependency-free SVG sparkline used to show a market's price trend.
 */
export default function Sparkline({
  data,
  width = 64,
  height = 20,
  stroke = "#00d4ff",
  fill = true,
  className,
}: SparklineProps) {
  if (!data || data.length === 0) {
    return <svg width={width} height={height} className={className} />;
  }

  const points = data.length === 1 ? [data[0], data[0]] : data;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);

  const coords = points.map((v, i) => {
    const x = i * step;
    const y = height - 1 - ((v - min) / range) * (height - 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const line = coords.join(" ");
  const area = `0,${height} ${line} ${width},${height}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      preserveAspectRatio="none"
    >
      {fill && <polygon points={area} fill={stroke} opacity="0.14" />}
      <polyline
        points={line}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx={coords[coords.length - 1].split(",")[0]}
        cy={coords[coords.length - 1].split(",")[1]}
        r="1.8"
        fill={stroke}
      />
    </svg>
  );
}
