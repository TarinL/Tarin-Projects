using InterviewApi.Data; 

namespace InterviewApi.Models;
/// <summary>
/// Used more as a data transfer object so that retrieving an interview object returns JSON
/// with User, Rubric and Zoom objects. 
/// </summary>
public class InterviewDetail
{
    public int Id { get; set;}
    public DateTime StartTime { get; set; }
    public string Status { get; set; }
    public string? Transcript { get; set; }
    public User User { get; set; }
    public Rubric Rubric { get; set; }
    public Zoom Zoom { get; set; }
    public Assignment Assignment { get; set; }
    public int Duration { get; set; }
    public DateTime DueDate { get; set; }
    public string? AdditionalInfo { get; set; }
    public int AssignmentId { get; set; }
    public string? StudentSubmission { get; set; }
    public int? ResultId { get; set; }   // FK -> result.id; equals interview.id once marked
}