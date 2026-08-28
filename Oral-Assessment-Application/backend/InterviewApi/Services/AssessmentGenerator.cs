using System.Text;
using System.Text.Json;
using InterviewApi.Models;

namespace InterviewApi.Services;

/// <summary>
/// Generates a knowledge-base formative assessment by calling OpenAI directly, and
/// emits it in the exact JSON-string shapes the DB columns expect (rubric.rubricContents
/// and assignment.questions) so no conversion layer is needed downstream. This is a C#
/// port of the Python kb_generator.py — the prompt text is kept identical so output
/// matches the proven CLI tool. If you change a prompt here, mirror it in
/// backend/interview_bot/kb_generator.py and vice versa.
/// </summary>
public class AssessmentGenerator
{
    private readonly HttpClient _http;
    private readonly string _apiKey;
    private readonly string _model;
    private readonly string _baseUrl;

    public AssessmentGenerator(HttpClient http, IConfiguration config)
    {
        _http = http;
        var section = config.GetSection("OpenAI");
        // Treat an empty/whitespace appsettings value as "not set" so the env var wins.
        var configured = section["ApiKey"];
        _apiKey = !string.IsNullOrWhiteSpace(configured)
                  ? configured
                  : (Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? "");
        _model = section["Model"] ?? "gpt-4o-mini";
        _baseUrl = (section["BaseUrl"] ?? "https://api.openai.com/v1").TrimEnd('/');
    }

    // ── Public orchestration ──────────────────────────────────────────────────

    public async Task<GeneratedAssessment> GenerateAsync(GenerateAssessmentRequest req)
    {
        string kb = (req.KnowledgeBase ?? "").Trim();
        if (kb.Length == 0)
            throw new ArgumentException("Knowledge base is empty.");
        if (req.NumQuestions < 1)
            throw new ArgumentException("NumQuestions must be at least 1.");

        List<RubricCriterion> rubric = string.IsNullOrWhiteSpace(req.Rubric)
            ? await GenerateRubricAsync(kb)
            : await NormalizeRubricAsync(req.Rubric!);

        List<QuestionItem> questions = await GenerateQuestionsAsync(kb, req.NumQuestions);

        // Serialize each into the exact JSON string the DB columns expect, so the
        // frontend persists them verbatim (rubric.rubricContents / assignment.questions).
        return new GeneratedAssessment
        {
            Rubric = SerializeRubric(rubric),
            Questions = SerializeQuestions(questions),
        };
    }

    // ── Reformatting arbitrary instructor uploads (LLM, content-preserving) ──────
    // These take free-form text (or already-structured JSON) and restructure it into
    // the DB-shaped JSON strings WITHOUT inventing or dropping content. Used by
    // AssessmentParser as the primary path, with a deterministic fallback.

    /// <summary>Reformat an instructor rubric (any format) into rubric.rubricContents JSON.</summary>
    public async Task<string> NormalizeRubricToJsonAsync(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Rubric text is empty.");
        List<RubricCriterion> rubric = await NormalizeRubricAsync(raw);
        return SerializeRubric(rubric);
    }

    /// <summary>Reformat instructor questions/areas-of-focus (any format) into assignment.questions JSON.</summary>
    public async Task<string> NormalizeQuestionsToJsonAsync(string raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            throw new ArgumentException("Questions text is empty.");
        List<QuestionItem> questions = await NormalizeQuestionsAsync(raw);
        return SerializeQuestions(questions);
    }

    private async Task<List<QuestionItem>> NormalizeQuestionsAsync(string raw)
    {
        // If already valid JSON in the expected shape, use it directly.
        try
        {
            using JsonDocument doc = JsonDocument.Parse(raw);
            List<QuestionItem> direct = CoerceQuestions(doc.RootElement.Clone());
            if (direct.Count > 0) return direct;
        }
        catch (JsonException)
        {
            // fall through to LLM normalisation
        }

        string system =
            "You convert an instructor's list of interview questions or areas of focus " +
            "into structured JSON WITHOUT changing their meaning. Preserve the " +
            "instructor's wording as closely as possible; do not invent new entries or " +
            "drop any. Treat each distinct question/area as one entry. " +
            "Return JSON of the form {\"questions\": [{\"text\": \"<the question or " +
            "area of focus, as the instructor intended it>\", \"weight\": <integer>}]}. " +
            "Preserve any weights the instructor specified; if weights are missing, " +
            "assign positive integers that sum to exactly 100.";
        JsonElement data = await JsonCallAsync(system, $"Questions to structure:\n\n{raw}");
        return CoerceQuestions(data);
    }

    private static List<QuestionItem> CoerceQuestions(JsonElement data)
    {
        JsonElement items;
        if (data.ValueKind == JsonValueKind.Object)
        {
            if (!data.TryGetProperty("questions", out items))
                throw new InvalidOperationException($"Could not find questions in: {data}");
        }
        else
        {
            items = data;
        }
        if (items.ValueKind != JsonValueKind.Array || items.GetArrayLength() == 0)
            throw new InvalidOperationException($"Could not find questions in: {data}");

        var questions = new List<QuestionItem>();
        foreach (JsonElement item in items.EnumerateArray())
        {
            if (item.ValueKind == JsonValueKind.String)
                questions.Add(new QuestionItem { Text = item.GetString() ?? "", Weight = 0 });
            else
                questions.Add(new QuestionItem { Text = GetString(item, "text"), Weight = GetInt(item, "weight") });
        }
        return questions;
    }

    // ── Serialization to the DB-shaped JSON strings ─────────────────────────────

    private static string SerializeRubric(List<RubricCriterion> rubric)
    {
        // {"<criterion>": {"description": "...", "weight": N}} — matches the
        // criterion-keyed dict stored in rubric.rubricContents.
        var dict = new Dictionary<string, object>();
        foreach (RubricCriterion c in rubric)
            dict[c.Criterion] = new { description = c.Description, weight = c.Weight };
        return JsonSerializer.Serialize(dict);
    }

    private static string SerializeQuestions(List<QuestionItem> questions)
    {
        // [{"text": "...", "weight": N}] — matches assignment.questions.
        var items = questions.Select(q => new { text = q.Text, weight = q.Weight });
        return JsonSerializer.Serialize(items);
    }

    // ── Rubric ──────────────────────────────────────────────────────────────────

    private const string RubricShape =
        "Return JSON of the form {\"rubric\": [{\"criterion\": \"<short name>\", " +
        "\"description\": \"<one or two sentences>\", \"weight\": <integer>}]}. " +
        "Weights must be positive integers that sum to exactly 100.";

    private async Task<List<RubricCriterion>> GenerateRubricAsync(string kb)
    {
        string system =
            "You design concise rubrics for LIGHT, FORMATIVE oral checks in a " +
            "flipped-classroom setting. The aim is to gauge whether a student has " +
            "done the required reading and understood the key ideas — not to conduct " +
            "a rigorous summative exam. Favour comprehension and retention over deep " +
            "critique. Produce between 4 and 6 criteria. " + RubricShape;
        string user =
            "Design a rubric for assessing student understanding of the following " +
            "course material:\n\n" +
            "--- BEGIN KNOWLEDGE BASE ---\n" +
            kb + "\n" +
            "--- END KNOWLEDGE BASE ---";

        JsonElement data = await JsonCallAsync(system, user);
        return CoerceRubric(data);
    }

    private async Task<List<RubricCriterion>> NormalizeRubricAsync(string raw)
    {
        // If the supplied rubric already parses as JSON in the expected shape, use it
        // directly; otherwise restructure it with a single LLM call.
        try
        {
            using JsonDocument doc = JsonDocument.Parse(raw);
            return CoerceRubric(doc.RootElement.Clone());
        }
        catch (JsonException)
        {
            // fall through to LLM normalisation
        }

        string system =
            "You convert a free-text rubric into structured JSON without changing " +
            "its meaning. " + RubricShape + " If the source omits weights, " +
            "distribute them sensibly so they still sum to 100.";
        JsonElement data = await JsonCallAsync(system, $"Rubric to structure:\n\n{raw}");
        return CoerceRubric(data);
    }

    private static List<RubricCriterion> CoerceRubric(JsonElement data)
    {
        JsonElement items;
        if (data.ValueKind == JsonValueKind.Object)
        {
            if (!data.TryGetProperty("rubric", out items) &&
                !data.TryGetProperty("criteria", out items))
                throw new InvalidOperationException($"Could not find a rubric list in: {data}");
        }
        else
        {
            items = data;
        }

        if (items.ValueKind != JsonValueKind.Array || items.GetArrayLength() == 0)
            throw new InvalidOperationException($"Could not find a rubric list in: {data}");

        var rubric = new List<RubricCriterion>();
        foreach (JsonElement item in items.EnumerateArray())
        {
            rubric.Add(new RubricCriterion
            {
                Criterion = GetString(item, "criterion"),
                Description = GetString(item, "description"),
                Weight = GetInt(item, "weight"),
            });
        }
        return rubric;
    }

    // ── Questions (areas of focus) ──────────────────────────────────────────────

    private async Task<List<QuestionItem>> GenerateQuestionsAsync(string kb, int num)
    {
        string system =
            "You design lines of questioning for a LIGHT, FORMATIVE oral check in a " +
            "flipped-classroom setting. Each entry is an AREA OF FOCUS that an " +
            "interview bot will later turn into its own spoken question at runtime; " +
            "the bot has the full knowledge base available and will phrase the " +
            "question itself (and vary it per student to deter cheating). Your job " +
            "is to tell the bot precisely WHERE to aim, not to write the question. " +
            "The goal is to surface whether the student actually engaged with the " +
            "material and understands it, including light application — not just " +
            "recall. " +
            $"Produce EXACTLY {num} distinct areas of focus that together give " +
            "good coverage of the material. Make them SPECIFIC and granular — anchor " +
            "each one to a concrete concept, claim, mechanism, or example drawn " +
            "directly from the knowledge base. Do NOT mirror broad assessment " +
            "categories or rubric-style headings; these areas of focus are meant to " +
            "be more pointed than that. " +
            "Return JSON of the form {\"questions\": [{\"text\": \"<a single " +
            "self-contained guidance string for the bot that names the focus area, " +
            "explains why probing it reveals genuine understanding, and describes the " +
            "specific angle/sub-topic to hone in on — guidance for the bot, NOT a " +
            "question to read aloud>\", \"weight\": <integer>}]}. The weight is the " +
            "relative importance of this area; weights must be positive integers that " +
            "sum to exactly 100.";
        string user =
            "Course material:\n" +
            "--- BEGIN KNOWLEDGE BASE ---\n" +
            kb + "\n" +
            "--- END KNOWLEDGE BASE ---";

        JsonElement data = await JsonCallAsync(system, user);

        JsonElement items;
        if (data.ValueKind == JsonValueKind.Object)
        {
            if (!data.TryGetProperty("questions", out items))
                throw new InvalidOperationException($"Could not find questions in: {data}");
        }
        else
        {
            items = data;
        }
        if (items.ValueKind != JsonValueKind.Array || items.GetArrayLength() == 0)
            throw new InvalidOperationException($"Could not find questions in: {data}");

        var questions = new List<QuestionItem>();
        foreach (JsonElement item in items.EnumerateArray())
        {
            questions.Add(new QuestionItem
            {
                Text = GetString(item, "text"),
                Weight = GetInt(item, "weight"),
            });
        }
        // Models occasionally over- or under-produce; enforce the requested count.
        if (questions.Count > num)
            questions = questions.GetRange(0, num);
        return questions;
    }

    private sealed class QuestionItem
    {
        public string Text { get; set; } = "";
        public int Weight { get; set; }
    }

    // ── OpenAI JSON-mode call ───────────────────────────────────────────────────

    private async Task<JsonElement> JsonCallAsync(string system, string user)
    {
        if (string.IsNullOrEmpty(_apiKey))
            throw new InvalidOperationException(
                "OpenAI API key is not configured — set OpenAI:ApiKey or the OPENAI_API_KEY env var.");

        var payload = new
        {
            model = _model,
            temperature = 0.4,
            response_format = new { type = "json_object" },
            messages = new[]
            {
                new { role = "system", content = system },
                new { role = "user", content = user },
            },
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, $"{_baseUrl}/chat/completions");
        request.Headers.Add("Authorization", $"Bearer {_apiKey}");
        request.Content = new StringContent(
            JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

        using HttpResponseMessage response = await _http.SendAsync(request);
        string body = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException(
                $"OpenAI returned {(int)response.StatusCode}: {body}");

        using JsonDocument doc = JsonDocument.Parse(body);
        string? content = doc.RootElement
            .GetProperty("choices")[0]
            .GetProperty("message")
            .GetProperty("content")
            .GetString();
        if (string.IsNullOrWhiteSpace(content))
            throw new InvalidOperationException("OpenAI returned empty content.");

        try
        {
            using JsonDocument parsed = JsonDocument.Parse(content);
            return parsed.RootElement.Clone();
        }
        catch (JsonException exc)
        {
            throw new InvalidOperationException($"LLM returned non-JSON output:\n{content}", exc);
        }
    }

    private static string GetString(JsonElement el, string prop)
    {
        if (el.TryGetProperty(prop, out JsonElement v) && v.ValueKind == JsonValueKind.String)
            return v.GetString() ?? "";
        if (el.TryGetProperty(prop, out v))
            return v.ToString();
        return "";
    }

    private static int GetInt(JsonElement el, string prop)
    {
        if (!el.TryGetProperty(prop, out JsonElement v))
            throw new InvalidOperationException($"Missing '{prop}' in rubric item: {el}");
        if (v.ValueKind == JsonValueKind.Number && v.TryGetInt32(out int n))
            return n;
        if (v.ValueKind == JsonValueKind.String && int.TryParse(v.GetString(), out int parsed))
            return parsed;
        throw new InvalidOperationException($"'{prop}' is not an integer in rubric item: {el}");
    }
}
