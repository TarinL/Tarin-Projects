namespace InterviewApi.Models;

/// <summary>
/// Request body for the deterministic parse endpoints
/// (POST /api/parse/rubric and POST /api/parse/questions).
/// Carries the raw plain-text the instructor uploaded.
/// </summary>
public class TextParseRequest
{
    public string? Text { get; set; }
}
