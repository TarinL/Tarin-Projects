namespace InterviewApi.Models;

/// <summary>
/// Request body for POST /api/assignment/generate-assessment.
/// Generates a formative rubric + lines of questioning from a knowledge base.
/// Nothing is persisted — the instructor edits the result, then saves it via the
/// assignment/rubric endpoints.
/// </summary>
public class GenerateAssessmentRequest
{
    public string KnowledgeBase { get; set; } = "";
    public int NumQuestions { get; set; } = 5;
    public string? Rubric { get; set; } // optional instructor-supplied rubric (JSON or free text) to normalise instead of generating
}
