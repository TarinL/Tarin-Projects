namespace InterviewApi.Models;

/// <summary>
/// Interview plus the nested User it belongs to. Inherits Interview so existing
/// top-level fields are unchanged; adds a nested user object for list endpoints.
/// </summary>
public class InterviewWithUser : Interview
{
    public User? User { get; set; }
}
