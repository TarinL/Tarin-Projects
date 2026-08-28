
using InterviewApi.Models;
using Microsoft.AspNetCore.SignalR;

namespace InterviewApi.Data
{
    public interface IInterviewRepository
    {
        Task<Interview?> GetInterviewByIdAsync(int id);
        Task<IEnumerable<InterviewWithUser>> GetInterviewByStudentIdAsync(int id);
        Task<int> AddInterviewAsync(Interview interview);
        Task<User?> GetUserByIdAsync(int studentId);
        Task<int> AddUserAsync(User user);
        Task<Rubric?> GetRubricByIdAsync(int id);
        Task<int> AddRubricAsync(Rubric rubric);
        Task<Zoom?> GetZoomByIdAsync(int id);
        Task<int> AddZoomAsync(Zoom zoom);
        Task<Result?> GetResultByIdAsync(int id);
        Task<int> AddResultAsync(Result result);
        Task<int> AddResultForInterviewAsync(int interviewId, Result result);
        Task<Assignment?> GetAssignmentByIdAsync(int id);
        Task<int> AddAssignmentAsync(Assignment assignment);
        Task UpdateAssignmentAsync(int id, Assignment assignment);
        Task UpdateInterviewAsync(int id, Interview interview);
        Task DeleteInterviewAsync(int id);
        Task DeleteAssignmentAsync(int id);
        Task FinishInterviewAsync(int id, string status, string? transcript);
        Task UpdateStudentSubmissionAsync(int id, string submission);
        Task<Instructor?> GetInstructorByIdAsync(int id);
        Task<int> AddInstructorAsync(Instructor instructor);
        Task<Class?> GetClassByIdAsync(int id);
        Task<int> AddClassAsync(Class c);
        Task AddStudentToClassAsync(int classId, int studentId);
        Task<IEnumerable<User>> GetStudentsByClassIdAsync(int classId);
        Task<IEnumerable<Assignment>> GetAssignmentsByClassIdAsync(int classId);
        Task<IEnumerable<Assignment>> GetAssignmentsByInstructorIdAsync(int instructorId);
        Task<IEnumerable<InterviewWithUser>> GetInterviewsByInstructorIdAsync(int instructorId);
        Task<IEnumerable<Class>> GetClassesByInstructorIdAsync(int instructorId);
    }
}

