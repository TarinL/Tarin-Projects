namespace InterviewApi.Models
{
    public class Interview
    {
        public int Id { get; set; }
        public int StudentId { get; set; }
        public int ZoomId {get; set; }
        public string? Transcript { get; set; }
        public DateTime StartTime { get; set; }
        public string Status { get; set; } = "SCHEDULED";
        public int Duration { get; set; }
        public DateTime DueDate { get; set; }
        public string? AdditionalInfo { get; set; }
        public int AssignmentId { get; set; }
        public string? StudentSubmission { get; set; } // per-student submitted work (submission mode)
        public int? ResultId { get; set; }             // FK -> result.id; equals interview.id once marked
    }
}

