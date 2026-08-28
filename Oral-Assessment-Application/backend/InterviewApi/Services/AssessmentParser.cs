using System.Text.Json;
using System.Text.RegularExpressions;
using InterviewApi.Models;

namespace InterviewApi.Services;

/// <summary>
/// Deterministic (no-LLM) parsers that turn an instructor's plain-text rubric or
/// questions upload into the exact JSON-string shapes the DB columns expect:
///   - Rubric    → rubric.rubricContents : {"&lt;criterion&gt;": {"description": "...", "weight": N}}
///   - Questions → assignment.questions   : [{"text": "...", "weight": N}]
///
/// Unlike <see cref="AssessmentGenerator"/> (which calls OpenAI to *generate* an
/// assessment), these parsers PRESERVE the instructor's content verbatim — they only
/// structure it. The output shapes are identical, so everything downstream
/// (config.py, marker.py) consumes them unchanged.
///
/// If the supplied text already parses as JSON in the expected shape it is normalised
/// and passed through untouched.
///
/// Accepted text formats (both forgiving and case-insensitive on weight keywords):
///
/// QUESTIONS — one area-of-focus per line. Leading list markers (-, *, 1., 1)) are
/// stripped. An optional weight may trail the line as "| 30", "(30%)", "(weight: 30)"
/// or "[30]". Lines without a weight have one filled in (see weight handling below).
///
/// RUBRIC — either:
///   (a) one criterion per line, pipe-delimited:  Name | description | 30
///       (description and weight are optional), or
///   (b) blank-line-separated blocks, where the first line is the criterion header
///       (with an optional weight token as above) and the remaining lines are its
///       description.
///
/// WEIGHTS — explicit weights are preserved exactly. If NO entry has a weight, weights
/// are split evenly to sum to 100. If only SOME entries have weights, the provided
/// values are kept and the missing ones are filled with the rounded average of the
/// provided values (so explicit instructor intent is never overwritten).
/// </summary>
public class AssessmentParser
{
    private readonly AssessmentGenerator _generator;

    public AssessmentParser(AssessmentGenerator generator)
    {
        _generator = generator;
    }

    // ── Public API: LLM reformat (primary) → deterministic parse → last resort ───
    // Designed to NEVER fail on non-empty input. The LLM restructures any format the
    // instructor throws at it; if it is unavailable or errors (no key, network, bad
    // output), a deterministic parser runs; if that somehow fails too, the raw text is
    // wrapped as a single entry so the upload is never lost.

    /// <summary>Reformat a questions upload into the assignment.questions JSON string.</summary>
    public async Task<string> ParseQuestionsAsync(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Questions text is empty.");
        try { return await _generator.NormalizeQuestionsToJsonAsync(raw); } catch { /* fall back */ }
        try { return DeterministicQuestions(raw); } catch { /* fall back */ }
        return JsonSerializer.Serialize(new[] { new { text = raw.Trim(), weight = 100 } });
    }

    /// <summary>Reformat a rubric upload into the rubric.rubricContents JSON string.</summary>
    public async Task<string> ParseRubricAsync(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Rubric text is empty.");
        try { return await _generator.NormalizeRubricToJsonAsync(raw); } catch { /* fall back */ }
        try { return DeterministicRubric(raw); } catch { /* fall back */ }
        var fallback = new Dictionary<string, object> { ["Overall"] = new { description = raw.Trim(), weight = 100 } };
        return JsonSerializer.Serialize(fallback);
    }

    // ── Deterministic fallback parsers ──────────────────────────────────────────

    /// <summary>Deterministically structure a questions upload (fallback path).</summary>
    private static string DeterministicQuestions(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Questions text is empty.");

        List<QuestionItem> items = TryQuestionsFromJson(raw) ?? QuestionsFromText(raw);
        if (items.Count == 0)
            throw new ArgumentException("No questions found in the supplied text.");

        int[] weights = FillWeights(items.Select(q => q.HasWeight ? (int?)q.Weight : null).ToList());
        var output = items.Select((q, i) => new { text = q.Text, weight = weights[i] });
        return JsonSerializer.Serialize(output);
    }

    /// <summary>Deterministically structure a rubric upload (fallback path).</summary>
    private static string DeterministicRubric(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Rubric text is empty.");

        List<RubricCriterion> criteria = TryRubricFromJson(raw) ?? RubricFromText(raw);
        if (criteria.Count == 0)
            throw new ArgumentException("No rubric criteria found in the supplied text.");

        int[] weights = FillWeights(criteria.Select(c => c.HasWeight ? (int?)c.Weight : null).ToList());

        // Criterion-keyed dict, matching rubric.rubricContents. Preserve insertion
        // order and disambiguate duplicate names with a numeric suffix.
        var dict = new Dictionary<string, object>();
        for (int i = 0; i < criteria.Count; i++)
        {
            string name = string.IsNullOrWhiteSpace(criteria[i].Criterion)
                ? $"Criterion {i + 1}"
                : criteria[i].Criterion.Trim();
            string key = name;
            int dup = 2;
            while (dict.ContainsKey(key))
                key = $"{name} ({dup++})";
            dict[key] = new { description = criteria[i].Description.Trim(), weight = weights[i] };
        }
        return JsonSerializer.Serialize(dict);
    }

    // ── Questions: text parsing ──────────────────────────────────────────────────

    private static List<QuestionItem> QuestionsFromText(string raw)
    {
        var items = new List<QuestionItem>();
        foreach (string rawLine in raw.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n'))
        {
            string line = StripListMarker(rawLine.Trim());
            if (line.Length == 0)
                continue;
            (string text, int? weight) = ExtractWeight(line);
            if (text.Length == 0)
                continue;
            items.Add(new QuestionItem { Text = text, Weight = weight ?? 0, HasWeight = weight.HasValue });
        }
        return items;
    }

    // ── Rubric: text parsing ─────────────────────────────────────────────────────

    private static List<RubricCriterion> RubricFromText(string raw)
    {
        string normalized = raw.Replace("\r\n", "\n").Replace('\r', '\n');

        // Records are blank-line-separated blocks; if there are no blank lines, each
        // non-empty line is its own record.
        bool hasBlankSeparators = Regex.IsMatch(normalized, "\n[ \t]*\n");
        IEnumerable<string[]> records = hasBlankSeparators
            ? Regex.Split(normalized, "\n[ \t]*\n")
                   .Select(block => block.Split('\n').Select(l => l.Trim()).Where(l => l.Length > 0).ToArray())
                   .Where(block => block.Length > 0)
            : normalized.Split('\n').Select(l => l.Trim()).Where(l => l.Length > 0)
                        .Select(l => new[] { l });

        var criteria = new List<RubricCriterion>();
        foreach (string[] record in records)
        {
            string header = record[0];

            // Pipe layout on the header line: Name | description | weight
            if (header.Contains('|'))
            {
                string[] parts = header.Split('|').Select(p => p.Trim()).ToArray();
                int? weight = null;
                int lastIdx = parts.Length - 1;
                if (parts.Length >= 2 && TryParseWeight(parts[lastIdx], out int w))
                {
                    weight = w;
                    lastIdx--;
                }
                string name = parts[0];
                string description = lastIdx >= 1
                    ? string.Join(" ", parts.Skip(1).Take(lastIdx))
                    : string.Join(" ", record.Skip(1));
                criteria.Add(new RubricCriterion
                {
                    Criterion = name,
                    Description = description,
                    Weight = weight ?? 0,
                    HasWeight = weight.HasValue,
                });
                continue;
            }

            // Header + description-lines layout.
            (string headerText, int? headerWeight) = ExtractWeight(StripListMarker(header));
            string desc = string.Join(" ", record.Skip(1));
            criteria.Add(new RubricCriterion
            {
                Criterion = headerText,
                Description = desc,
                Weight = headerWeight ?? 0,
                HasWeight = headerWeight.HasValue,
            });
        }
        return criteria;
    }

    // ── JSON pass-through (already-structured uploads) ───────────────────────────

    private static List<QuestionItem>? TryQuestionsFromJson(string raw)
    {
        string trimmed = raw.TrimStart();
        if (!trimmed.StartsWith('[') && !trimmed.StartsWith('{'))
            return null;
        try
        {
            using JsonDocument doc = JsonDocument.Parse(raw);
            JsonElement root = doc.RootElement;
            JsonElement arr = root;
            if (root.ValueKind == JsonValueKind.Object && root.TryGetProperty("questions", out JsonElement q))
                arr = q;
            if (arr.ValueKind != JsonValueKind.Array)
                return null;

            var items = new List<QuestionItem>();
            foreach (JsonElement el in arr.EnumerateArray())
            {
                if (el.ValueKind == JsonValueKind.String)
                {
                    items.Add(new QuestionItem { Text = el.GetString() ?? "", Weight = 0, HasWeight = false });
                }
                else
                {
                    int? w = TryGetInt(el, "weight");
                    items.Add(new QuestionItem
                    {
                        Text = GetString(el, "text"),
                        Weight = w ?? 0,
                        HasWeight = w.HasValue,
                    });
                }
            }
            return items.Count > 0 ? items : null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static List<RubricCriterion>? TryRubricFromJson(string raw)
    {
        string trimmed = raw.TrimStart();
        if (!trimmed.StartsWith('[') && !trimmed.StartsWith('{'))
            return null;
        try
        {
            using JsonDocument doc = JsonDocument.Parse(raw);
            JsonElement root = doc.RootElement;
            var criteria = new List<RubricCriterion>();

            if (root.ValueKind == JsonValueKind.Object)
            {
                // Either the criterion-keyed dict shape, or {"rubric": [...]}.
                if (root.TryGetProperty("rubric", out JsonElement listEl) && listEl.ValueKind == JsonValueKind.Array)
                {
                    foreach (JsonElement el in listEl.EnumerateArray())
                        criteria.Add(CriterionFromObject(GetString(el, "criterion"), el));
                }
                else
                {
                    foreach (JsonProperty prop in root.EnumerateObject())
                        criteria.Add(CriterionFromObject(prop.Name, prop.Value));
                }
            }
            else if (root.ValueKind == JsonValueKind.Array)
            {
                foreach (JsonElement el in root.EnumerateArray())
                    criteria.Add(CriterionFromObject(GetString(el, "criterion"), el));
            }
            else
            {
                return null;
            }
            return criteria.Count > 0 ? criteria : null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static RubricCriterion CriterionFromObject(string name, JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.String)
            return new RubricCriterion { Criterion = name, Description = value.GetString() ?? "", HasWeight = false };
        int? w = TryGetInt(value, "weight");
        return new RubricCriterion
        {
            Criterion = name,
            Description = GetString(value, "description"),
            Weight = w ?? 0,
            HasWeight = w.HasValue,
        };
    }

    // ── Weight handling ──────────────────────────────────────────────────────────

    /// <summary>
    /// Fill missing weights without overwriting explicit ones. All provided → kept as-is.
    /// None provided → even split summing to 100. Some provided → keep them and fill the
    /// gaps with the rounded average of the provided values.
    /// </summary>
    private static int[] FillWeights(IReadOnlyList<int?> weights)
    {
        int n = weights.Count;
        var result = new int[n];
        List<int> provided = weights.Where(w => w.HasValue).Select(w => w!.Value).ToList();

        if (provided.Count == n)
        {
            for (int i = 0; i < n; i++) result[i] = weights[i]!.Value;
            return result;
        }

        if (provided.Count == 0)
        {
            int baseW = 100 / n;
            int remainder = 100 - baseW * n; // distributed to the first `remainder` items
            for (int i = 0; i < n; i++) result[i] = baseW + (i < remainder ? 1 : 0);
            return result;
        }

        int fill = (int)Math.Round(provided.Average(), MidpointRounding.AwayFromZero);
        if (fill < 1) fill = 1;
        for (int i = 0; i < n; i++) result[i] = weights[i].HasValue ? weights[i]!.Value : fill;
        return result;
    }

    private static readonly Regex WeightToken = new(
        @"[\(\[]\s*(?:weights?\s*[:=]?\s*)?(\d{1,3})\s*%?\s*[\)\]]\s*$",
        RegexOptions.IgnoreCase | RegexOptions.Compiled);

    /// <summary>
    /// Strip a trailing weight token from a line and return (cleanedText, weight?).
    /// Recognises "| 30", "(30)", "(30%)", "(weight: 30)", "[30]".
    /// </summary>
    private static (string text, int? weight) ExtractWeight(string line)
    {
        // Pipe form: take the segment after the LAST pipe if it is a bare integer.
        int pipe = line.LastIndexOf('|');
        if (pipe >= 0 && TryParseWeight(line[(pipe + 1)..], out int pw))
            return (line[..pipe].Trim(), pw);

        Match m = WeightToken.Match(line);
        if (m.Success && int.TryParse(m.Groups[1].Value, out int bw))
            return (line[..m.Index].Trim(), bw);

        return (line.Trim(), null);
    }

    private static bool TryParseWeight(string token, out int weight)
    {
        weight = 0;
        string t = token.Trim().TrimEnd('%').Trim();
        return int.TryParse(t, out weight);
    }

    private static readonly Regex ListMarker = new(@"^\s*(?:[-*•]|\d+[\.\)])\s+", RegexOptions.Compiled);

    private static string StripListMarker(string line) => ListMarker.Replace(line, "");

    // ── JSON element helpers (mirrors AssessmentGenerator) ───────────────────────

    private static string GetString(JsonElement el, string prop)
    {
        if (el.ValueKind == JsonValueKind.Object && el.TryGetProperty(prop, out JsonElement v))
            return v.ValueKind == JsonValueKind.String ? (v.GetString() ?? "") : v.ToString();
        return "";
    }

    private static int? TryGetInt(JsonElement el, string prop)
    {
        if (el.ValueKind != JsonValueKind.Object || !el.TryGetProperty(prop, out JsonElement v))
            return null;
        if (v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out int n)) return n;
        if (v.ValueKind == JsonValueKind.String && int.TryParse(v.GetString(), out int p)) return p;
        return null;
    }

    private sealed class QuestionItem
    {
        public string Text { get; set; } = "";
        public int Weight { get; set; }
        public bool HasWeight { get; set; }
    }
}
