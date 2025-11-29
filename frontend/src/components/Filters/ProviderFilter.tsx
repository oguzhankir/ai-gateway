/** Provider filter component */

'use client';

interface ProviderFilterProps {
  selected: string | null;
  onChange: (provider: string | null) => void;
}

export function ProviderFilter({ selected, onChange }: ProviderFilterProps) {
  const providers = ['All', 'OpenAI', 'Gemini'];

  return (
    <select
      value={selected || 'All'}
      onChange={(e) => onChange(e.target.value === 'All' ? null : e.target.value)}
      className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      {providers.map((p) => (
        <option key={p} value={p}>
          {p}
        </option>
      ))}
    </select>
  );
}
