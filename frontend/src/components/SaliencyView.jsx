/**
 * Renders original text with each sentence highlighted by its saliency score.
 * Score 0 = cool blue-grey, Score 1 = vivid amber/gold.
 */

function scoreToColor(score) {
  // Interpolate from #1e293b (low) through #4ade80 (mid) to #f59e0b (high)
  if (score < 0.5) {
    const t = score * 2;
    const r = Math.round(30 + t * (74 - 30));
    const g = Math.round(41 + t * (222 - 41));
    const b = Math.round(59 + t * (128 - 59));
    return `rgb(${r},${g},${b})`;
  } else {
    const t = (score - 0.5) * 2;
    const r = Math.round(74 + t * (245 - 74));
    const g = Math.round(222 + t * (158 - 222));
    const b = Math.round(128 + t * (11 - 128));
    return `rgb(${r},${g},${b})`;
  }
}

function scoreToOpacity(score) {
  return 0.12 + score * 0.55;
}

export default function SaliencyView({ sentences, onHover, hoveredIdx }) {
  if (!sentences || sentences.length === 0) return null;

  return (
    <div className="saliency-text">
      {sentences.map((s) => {
        const bg = scoreToColor(s.score);
        const opacity = scoreToOpacity(s.score);
        const isHovered = hoveredIdx === s.index;

        return (
          <span
            key={s.index}
            className={`saliency-sentence ${isHovered ? "hovered" : ""}`}
            style={{
              backgroundColor: bg,
              opacity: isHovered ? 1 : opacity + 0.1,
              boxShadow: isHovered ? `0 0 0 2px ${bg}` : "none",
            }}
            onMouseEnter={() => onHover(s.index)}
            onMouseLeave={() => onHover(null)}
            title={`Attention score: ${(s.score * 100).toFixed(0)}%`}
          >
            {s.text}{" "}
          </span>
        );
      })}
    </div>
  );
}
