namespace InterviewApi.Models;

public class Class
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int InstructorId { get; set; }   // owning instructor (instructor.id)
}
