'use client';

import { useEffect, useRef, useState } from 'react';

interface ChapterChartProps {
  data: {
    action: number;
    value: number;
    mult: number;
    desc: string;
  }[];
  onActionClick?: (index: number) => void;
}

export default function ChapterChart({ data, onActionClick }: ChapterChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [activePoint, setActivePoint] = useState<number | null>(null);
  const [tooltipData, setTooltipData] = useState<any>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = svgRef.current;
    const width = svg.clientWidth;
    const height = svg.clientHeight;
    const padding = { top: 30, right: 30, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value));

    // Clear previous content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Create defs for gradient
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'gradient-chapter');
    gradient.setAttribute('x1', '0%');
    gradient.setAttribute('y1', '0%');
    gradient.setAttribute('x2', '0%');
    gradient.setAttribute('y2', '100%');
    
    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('style', 'stop-color:#FFFFFF;stop-opacity:0.08');
    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%');
    stop2.setAttribute('style', 'stop-color:#FFFFFF;stop-opacity:0');
    
    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.appendChild(defs);

    // Draw grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i;
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', padding.left.toString());
      line.setAttribute('y1', y.toString());
      line.setAttribute('x2', (width - padding.right).toString());
      line.setAttribute('y2', y.toString());
      line.setAttribute('stroke', 'rgba(255, 255, 255, 0.05)');
      line.setAttribute('stroke-width', '1');
      svg.appendChild(line);

      // Y-axis label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', (padding.left - 10).toString());
      text.setAttribute('y', (y + 4).toString());
      text.setAttribute('text-anchor', 'end');
      text.setAttribute('class', 'fill-text-tertiary text-[11px] font-mono');
      text.textContent = (maxValue - (maxValue - minValue) * (i / 4)).toFixed(0);
      svg.appendChild(text);
    }

    // Build area path
    let areaData = '';
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - ((d.value - minValue) / (maxValue - minValue)) * chartHeight;

      if (i === 0) {
        areaData = `M ${x} ${height - padding.bottom} L ${x} ${y}`;
      } else {
        areaData += ` L ${x} ${y}`;
      }
    });
    areaData += ` L ${padding.left + chartWidth} ${height - padding.bottom} Z`;

    // Draw area
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    area.setAttribute('d', areaData);
    area.setAttribute('fill', 'url(#gradient-chapter)');
    svg.appendChild(area);

    // Draw line segments
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - ((d.value - minValue) / (maxValue - minValue)) * chartHeight;

      if (i > 0) {
        const prevX = padding.left + (chartWidth / (data.length - 1)) * (i - 1);
        const prevY = padding.top + chartHeight - ((data[i - 1].value - minValue) / (maxValue - minValue)) * chartHeight;

        const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        line.setAttribute('d', `M ${prevX} ${prevY} L ${x} ${y}`);
        line.setAttribute('fill', 'none');
        line.setAttribute('stroke', d.mult >= 1 ? '#10B981' : '#EF4444');
        line.setAttribute('stroke-width', '2.5');
        line.setAttribute('stroke-linecap', 'round');
        line.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(line);
      }

      // X-axis label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', x.toString());
      text.setAttribute('y', (height - padding.bottom + 20).toString());
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('class', 'fill-text-tertiary text-[11px] font-mono');
      text.textContent = d.action === 0 ? 'Start' : d.action.toString();
      svg.appendChild(text);
    });

    // Draw points
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - ((d.value - minValue) / (maxValue - minValue)) * chartHeight;

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', x.toString());
      circle.setAttribute('cy', y.toString());
      circle.setAttribute('r', activePoint === i ? '7' : '5');
      circle.setAttribute('fill', '#FFFFFF');
      circle.setAttribute('stroke', '#0F0F0F');
      circle.setAttribute('stroke-width', '3');
      circle.setAttribute('class', 'cursor-pointer transition-all hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]');
      circle.setAttribute('data-index', i.toString());

      circle.addEventListener('mouseenter', (e) => {
        setActivePoint(i);
        const prevValue = i > 0 ? data[i - 1].value : d.value / d.mult;
        setTooltipData({
          action: d.action,
          mult: d.mult,
          desc: d.desc,
          before: prevValue,
          after: d.value,
          isStart: d.action === 0,
        });
        
        const rect = svg.getBoundingClientRect();
        setTooltipPosition({
          x: e.clientX - 250, // Position to the left of cursor
          y: rect.top + y - 20,
        });
      });

      circle.addEventListener('mouseleave', () => {
        setActivePoint(null);
        setTooltipData(null);
      });

      circle.addEventListener('click', () => {
        // Don't trigger action click for starting point
        if (d.action === 0) return;
        if (onActionClick) onActionClick(i);
      });

      svg.appendChild(circle);
    });
  }, [data, activePoint, onActionClick]);

  return (
    <div className="relative pr-24">
      <svg
        ref={svgRef}
        className="w-full h-[300px]"
      />
      
      {tooltipData && (
        <div
          ref={tooltipRef}
          className="fixed z-50 bg-gradient-to-br from-surface-light to-surface border border-white/20 rounded-xl p-4 max-w-[400px] shadow-[0_20px_40px_rgba(0,0,0,0.6),0_0_60px_rgba(255,255,255,0.1)] pointer-events-none"
          style={{
            left: tooltipPosition.x + 'px',
            top: tooltipPosition.y + 'px',
            transform: 'translate(0, -100%)',
          }}
        >
          <div className="flex justify-between items-center mb-3 pb-3 border-b border-white/10">
            <span className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
              {tooltipData.isStart ? 'Starting Stock' : `Action ${tooltipData.action}`}
            </span>
            {!tooltipData.isStart && (
              <span className={`font-mono text-lg font-semibold ${tooltipData.mult >= 1 ? 'text-accent-positive drop-shadow-[0_0_10px_rgba(16,185,129,0.4)]' : 'text-accent-negative drop-shadow-[0_0_10px_rgba(239,68,68,0.4)]'}`}>
                {tooltipData.mult.toFixed(2)}x {tooltipData.mult >= 1 ? '↑' : '↓'}
              </span>
            )}
          </div>
          <div className="text-sm leading-relaxed text-[#D4D4D4] mb-3">
            {tooltipData.desc}
          </div>
          {tooltipData.isStart ? (
            <div className="text-xs text-text-secondary pt-3 border-t border-white/10 text-center">
              Stock Value: <span className="font-mono text-text-primary font-medium text-base">{tooltipData.after.toFixed(1)}</span>
            </div>
          ) : (
            <div className="flex justify-between text-xs text-text-secondary pt-3 border-t border-white/10">
              <div>Before: <span className="font-mono text-text-primary font-medium">{tooltipData.before.toFixed(1)}</span></div>
              <div>→</div>
              <div>After: <span className="font-mono text-text-primary font-medium">{tooltipData.after.toFixed(1)}</span></div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

