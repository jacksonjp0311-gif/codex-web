# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
const OpenAI = require("openai");

(async () => {
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const r = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: "Reply with ONLY a JSON array of {path,description} items. No extra text or fences."
      },
      {
        role: "user",
        content: "Project Context: Current Codex Web approval-ui flows\n\nList the next API endpoints as a JSON array."
      }
    ],
    temperature: 0.7,
    max_tokens: 200
  });

  let text = r.choices[0].message.content.trim();

  // strip Markdown fences
  if (text.startsWith("```")) {
    text = text.replace(/^```(?:json)?\s*/, "").replace(/```$/, "").trim();
  }

  // extract from first [ to last ] (or to end if missing)
  const start = text.indexOf("[");
  const end   = text.lastIndexOf("]");
  if (start >= 0) {
    text = end >= start ? text.slice(start, end + 1) : text.slice(start);
  }

  // auto-balance braces
  const opens  = (text.match(/\{/g) || []).length;
  const closes = (text.match(/\}/g) || []).length;
  if (opens > closes) {
    text += "}".repeat(opens - closes);
  }

  // attempt parse, drop trailing element on failure
  let arr;
  try {
    arr = JSON.parse(text);
  } catch (firstErr) {
    const lastComma = text.lastIndexOf("},");
    if (lastComma > 0) {
      // drop the last incomplete element
      text = text.slice(0, lastComma + 1) + "]";
      try {
        arr = JSON.parse(text);
      } catch (secondErr) {
        console.error("❌ JSON parse error after element-drop:", text);
        process.exit(1);
      }
    } else {
      console.error("❌ JSON parse error (no comma-separable element):", text);
      process.exit(1);
    }
  }

  console.log(JSON.stringify(arr, null, 2));
})();

