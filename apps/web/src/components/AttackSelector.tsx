export type AttackType =
  | "DOS"
  | "XSS/SQL Injection"
  | "Port Probing"
  | "Brute Force"
  | "Slowloris";

type Props = {
  value: AttackType;
  onChange: (v: AttackType) => void;
};

export default function AttackSelector({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="attack-type" className="text-sm font-medium text-gray-100">
        Attack Type
      </label>
      <select
        id="attack-type"
        value={value}
        onChange={(e) => onChange(e.target.value as AttackType)}
        className="w-52 rounded-md border border-white/20 bg-white/10 px-3 py-2 text-white shadow-inner focus:border-white focus:outline-none focus:ring-1 focus:ring-white"
      >
        <option value="Port Probing">Port Probing</option>
        <option value="DOS">DOS</option>
        <option value="XSS/SQL Injection">XSS/SQL Injection</option>
        <option value="Brute Force">Brute Force</option>
        <option value="Slowloris">Slowloris</option>
      </select>
    </div>
  );
}
