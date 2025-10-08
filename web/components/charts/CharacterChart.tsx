'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

interface CharacterChartProps {
  data: {
    chapter: number;
    value: number;
    change?: number;
    description?: string;
  }[];
  characterName: string;
}

export default function CharacterChart({ data, characterName }: CharacterChartProps) {
  const router = useRouter();
  const svgRef = useRef<SVGSVGElement>(null);
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
    const minValue = 0;

    // Clear previous content
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }

    // Create defs for gradient
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'gradient-character');
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
      text.textContent = (maxValue - (maxValue / 4) * i).toFixed(0);
      svg.appendChild(text);
    }

    // Build area path
    let areaData = '';
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - (d.value / maxValue) * chartHeight;

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
    area.setAttribute('fill', 'url(#gradient-character)');
    svg.appendChild(area);

    // Draw line segments
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - (d.value / maxValue) * chartHeight;

      if (i > 0) {
        const prevX = padding.left + (chartWidth / (data.length - 1)) * (i - 1);
        const prevY = padding.top + chartHeight - (data[i - 1].value / maxValue) * chartHeight;

        const isGain = d.value > data[i - 1].value;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        line.setAttribute('d', `M ${prevX} ${prevY} L ${x} ${y}`);
        line.setAttribute('fill', 'none');
        line.setAttribute('stroke', isGain ? '#10B981' : '#EF4444');
        line.setAttribute('stroke-width', '2.5');
        line.setAttribute('stroke-linecap', 'round');
        line.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(line);
      }

      // X-axis labels (every few points based on data length)
      const labelFrequency = Math.ceil(data.length / 10);
      if (i % labelFrequency === 0 || i === data.length - 1 || i === 0) {
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', x.toString());
        text.setAttribute('y', (height - padding.bottom + 20).toString());
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('class', 'fill-text-tertiary text-[11px] font-mono');
        // Show "Start" for the initial point, otherwise show chapter number
        text.textContent = i === 0 && d.chapter < 1 ? 'Start' : `Ch ${Math.round(d.chapter)}`;
        svg.appendChild(text);
      }
    });

    // Draw points
    data.forEach((d, i) => {
      const x = padding.left + (chartWidth / (data.length - 1)) * i;
      const y = padding.top + chartHeight - (d.value / maxValue) * chartHeight;

      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', x.toString());
      circle.setAttribute('cy', y.toString());
      circle.setAttribute('r', activePoint === i ? '7' : '4');
      circle.setAttribute('fill', '#FFFFFF');
      circle.setAttribute('stroke', '#0F0F0F');
      circle.setAttribute('stroke-width', '3');
      // Make starting point non-clickable
      const cursorClass = (i === 0 && d.chapter < 1) ? 'cursor-default' : 'cursor-pointer';
      circle.setAttribute('class', `${cursorClass} transition-all hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.6)]`);

      circle.addEventListener('mouseenter', (e) => {
        setActivePoint(i);
        const prevValue = i > 0 ? data[i - 1].value : 0;
        const changePercent = prevValue > 0 ? ((d.value - prevValue) / prevValue) * 100 : 0;
        setTooltipData({
          chapter: i === 0 && d.chapter < 1 ? 'Start' : `Chapter ${Math.round(d.chapter)}`,
          value: d.value,
          before: prevValue,
          change: d.value - prevValue,
          changePercent,
          description: d.description || '',
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
        // Don't navigate if it's the starting point
        if (i === 0 && d.chapter < 1) return;
        router.push(`/chapter/${Math.round(d.chapter)}?character=${encodeURIComponent(characterName)}`);
      });

      svg.appendChild(circle);
    });
  }, [data, activePoint, characterName, router]);

  return (
    <div className="relative pr-24">
      <svg
        ref={svgRef}
        className="w-full h-[300px]"
      />
      
      {tooltipData && (
        <div
          className="fixed z-50 bg-gradient-to-br from-surface-light to-surface border border-white/20 rounded-xl p-4 max-w-[500px] shadow-[0_20px_40px_rgba(0,0,0,0.6),0_0_60px_rgba(255,255,255,0.1)] pointer-events-none"
          style={{
            left: tooltipPosition.x + 'px',
            top: tooltipPosition.y + 'px',
            transform: 'translate(0, -100%)',
          }}
        >
          <div className="flex justify-between items-center mb-3 pb-3 border-b border-white/10">
            <span className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
              {tooltipData.chapter}
            </span>
            {tooltipData.chapter !== 'Start' && (
              <span className={`font-mono text-lg font-semibold ${tooltipData.change >= 0 ? 'text-accent-positive drop-shadow-[0_0_10px_rgba(16,185,129,0.4)]' : 'text-accent-negative drop-shadow-[0_0_10px_rgba(239,68,68,0.4)]'}`}>
                {tooltipData.change >= 0 ? '+' : ''}{tooltipData.change.toFixed(1)} ({tooltipData.changePercent >= 0 ? '+' : ''}{tooltipData.changePercent.toFixed(1)}%)
              </span>
            )}
          </div>
          
          {tooltipData.description && (
            <div className="text-sm leading-relaxed text-[#D4D4D4] mb-3 max-h-[200px] overflow-y-auto">
              {tooltipData.description.split(' | ').map((action: string, i: number) => (
                <div key={i} className="mb-2 last:mb-0">
                  <span className="text-text-tertiary text-xs font-mono mr-2">{i + 1}.</span>
                  {action}
                </div>
              ))}
            </div>
          )}
          
          {tooltipData.chapter === 'Start' ? (
            <div className="text-xs text-text-secondary pt-3 border-t border-white/10 text-center">
              Initial Stock: <span className="font-mono text-text-primary font-medium text-base">{tooltipData.value.toFixed(1)}</span>
            </div>
          ) : (
            <>
              <div className="flex justify-between text-xs text-text-secondary pt-3 border-t border-white/10 mb-3">
                <div>Before: <span className="font-mono text-text-primary font-medium">{tooltipData.before.toFixed(1)}</span></div>
                <div>→</div>
                <div>After: <span className="font-mono text-text-primary font-medium">{tooltipData.value.toFixed(1)}</span></div>
              </div>
              <div className="pt-3 border-t border-white/10 text-[11px] text-text-tertiary italic text-center">
                Click to view detailed chapter analysis
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

