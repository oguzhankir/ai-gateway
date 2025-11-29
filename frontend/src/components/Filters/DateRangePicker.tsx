/** Date range picker component */

'use client';

import { useState, useEffect } from 'react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';

interface DateRangePickerProps {
  onChange: (start: string | undefined, end: string | undefined) => void;
}

export function DateRangePicker({ onChange }: DateRangePickerProps) {
  const [preset, setPreset] = useState<string>('7d');

  const presets = {
    '24h': { start: subDays(new Date(), 1), end: new Date() },
    '7d': { start: subDays(new Date(), 7), end: new Date() },
    '30d': { start: subDays(new Date(), 30), end: new Date() },
    custom: null,
  };

  const handlePresetChange = (newPreset: string) => {
    setPreset(newPreset);
    if (newPreset !== 'custom' && presets[newPreset as keyof typeof presets]) {
      const range = presets[newPreset as keyof typeof presets]!;
      onChange(
        format(startOfDay(range.start), "yyyy-MM-dd'T'HH:mm:ss"),
        format(endOfDay(range.end), "yyyy-MM-dd'T'HH:mm:ss")
      );
    } else {
      // Clear dates for custom
      onChange(undefined, undefined);
    }
  };

  // Set default preset on mount
  useEffect(() => {
    if (preset === '7d') {
      const range = presets['7d'];
      onChange(
        format(startOfDay(range.start), "yyyy-MM-dd'T'HH:mm:ss"),
        format(endOfDay(range.end), "yyyy-MM-dd'T'HH:mm:ss")
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  return (
    <div className="flex gap-2">
      {Object.keys(presets).map((p) => (
        <button
          key={p}
          onClick={() => handlePresetChange(p)}
          className={`px-4 py-2 rounded ${
            preset === p
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {p === '24h' ? 'Last 24h' : p === '7d' ? 'Last 7d' : p === '30d' ? 'Last 30d' : 'Custom'}
        </button>
      ))}
    </div>
  );
}
