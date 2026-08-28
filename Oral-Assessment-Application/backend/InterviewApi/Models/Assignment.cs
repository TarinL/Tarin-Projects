namespace InterviewApi.Models;

public class Assignment
{
    public int Id { get; set; }
    public string? Name { get; set; } // nullable
    public string Contents { get; set; }
    public string Mode { get; set; } = "manual"; // manual | submission | knowledge_base
    public string? KnowledgeBase { get; set; }   // instructor-provided course content (knowledge_base mode)
    public string? Questions { get; set; }       // JSON array of {text, weight}
    public int? ClassId { get; set; }             // owning class (class.id); null for class-less assignments
    public int? RubricId { get; set; }            // owning rubric (rubric.id); the assignment owns its rubric
}