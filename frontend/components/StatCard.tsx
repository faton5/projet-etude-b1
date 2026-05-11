export function StatCard({
  label,
  value,
  tone = "default"
}: {
  label: string;
  value: string;
  tone?: "default" | "leaf" | "tomato" | "soil";
}) {
  const tones = {
    default: "border-ink/10 bg-white/80 text-ink",
    leaf: "border-leaf/20 bg-leaf/10 text-leaf",
    tomato: "border-tomato/25 bg-tomato/10 text-tomato",
    soil: "border-soil/20 bg-soil/10 text-soil"
  };

  return (
    <div className={`rounded-lg border p-4 shadow-soft ${tones[tone]}`}>
      <p className="text-sm font-semibold opacity-75">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </div>
  );
}
