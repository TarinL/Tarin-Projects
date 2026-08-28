namespace InterviewApi.Models;

/// <summary>
/// Response for POST /api/assignment/generate-assessment.
///
/// Both fields are emitted as JSON STRINGS in exactly the shape the DB columns
/// expect, so the frontend can persist them with no conversion:
///   - Rubric    → rubric.rubricContents : {"<criterion>": {"description": "...", "weight": N}}
///   - Questions → assignment.questions   : [{"text": "...", "weight": N}]
/// </summary>
public class GeneratedAssessment
{
    public string Rubric { get; set; } = "";
    public string Questions { get; set; } = "";
}

/// <summary>Internal generation shape for a single rubric criterion (not part of the response).</summary>
public class RubricCriterion
{
    public string Criterion { get; set; } = "";
    public string Description { get; set; } = "";
    public int Weight { get; set; }

    /// <summary>True when an explicit weight was supplied (vs. one to be filled in).
    /// Used by AssessmentParser to avoid overwriting instructor-provided weights.</summary>
    public bool HasWeight { get; set; }
}
