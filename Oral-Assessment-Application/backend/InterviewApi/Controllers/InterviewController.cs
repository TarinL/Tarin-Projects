using Amazon.ECS;
using Amazon.ECS.Model;
using Microsoft.AspNetCore.Mvc;
using InterviewApi.Models;
using InterviewApi.Data;
using InterviewApi.Services;

namespace InterviewApi.Controllers;

[Route("api")]
[ApiController]
public class InterviewController : ControllerBase
{
    private readonly IInterviewRepository _interviewRepository;
    private readonly IAmazonECS _ecs;
    private readonly IConfiguration _config;
    private readonly AssessmentGenerator _assessmentGenerator;
    private readonly AssessmentParser _assessmentParser;

    public InterviewController(IInterviewRepository interviewRepository, IAmazonECS ecs, IConfiguration config, AssessmentGenerator assessmentGenerator, AssessmentParser assessmentParser)
    {
        _interviewRepository = interviewRepository;
        _ecs = ecs;
        _config = config;
        _assessmentGenerator = assessmentGenerator;
        _assessmentParser = assessmentParser;
    }

    [HttpGet("interview/{id}")]
    public async Task<ActionResult<InterviewDetail>> GetInterview(int id)
    {
        Interview interview = await _interviewRepository.GetInterviewByIdAsync(id);
        if (interview == null)
        {
            return NotFound("Interview not found");
        }
        User user = await _interviewRepository.GetUserByIdAsync(interview.StudentId);
        Zoom zoom = await _interviewRepository.GetZoomByIdAsync(interview.ZoomId);
        // Assignment carries the mode / knowledge_base / questions the bot needs,
        // and now owns the rubric. May be null for legacy interviews with no (or a
        // missing) assignment_id.
        Assignment assignment = await _interviewRepository.GetAssignmentByIdAsync(interview.AssignmentId);
        Rubric rubric = assignment?.RubricId is int rubricId
            ? await _interviewRepository.GetRubricByIdAsync(rubricId)
            : null;

        InterviewDetail fullInterview = new InterviewDetail
        {
            Id         = interview.Id,
            StartTime  = interview.StartTime,
            Status     = interview.Status,
            Transcript = interview.Transcript,
            User       = user!,
            Rubric     = rubric!,
            Zoom       = zoom!,
            Assignment = assignment!,
            Duration = interview.Duration,
            DueDate  = interview.DueDate,
            AdditionalInfo = interview.AdditionalInfo,
            AssignmentId = interview.AssignmentId,
            StudentSubmission = interview.StudentSubmission,
            ResultId = interview.ResultId,
        };
        return Ok(fullInterview);
    }

    [HttpGet("interview/studentid/{id}")]
    public async Task<ActionResult<IEnumerable<InterviewWithUser>>> GetInterviewsByStudentId(int id)
    {
        User student = await _interviewRepository.GetUserByIdAsync(id);
        if (student == null)
        {
            return NotFound("User does not exist");
        }
        IEnumerable<InterviewWithUser> interviews = await _interviewRepository.GetInterviewByStudentIdAsync(id);
        return Ok(interviews);
    }


    [HttpPost("interview")]
    public async Task<ActionResult<string>> AddInterview(Interview interview)
    {
        int id = await _interviewRepository.AddInterviewAsync(interview);
        return Ok($"Interview added. Interview Id: {id}");
    }
    
    [HttpPut("interview/{id}")]
    public async Task<ActionResult<String>> UpdateInterview(int id, Interview interview)
    {
        Interview i = await _interviewRepository.GetInterviewByIdAsync(id);
        if (i == null)
        {
            return NotFound($"Interview with id {id} not found");
        }
        await _interviewRepository.UpdateInterviewAsync(id, interview);
        return Ok($"Interview updated. Interview Id: {id}");
    }

    [HttpPatch("interview/{id}/finish")]
    public async Task<ActionResult<string>> FinishInterview(int id, InterviewFinishRequest request)
    {
        if (request.Status != "COMPLETED" && request.Status != "FAILED")
        {
            return BadRequest("Status must be COMPLETED or FAILED");
        }
        Interview existing = await _interviewRepository.GetInterviewByIdAsync(id);
        if (existing == null)
        {
            return NotFound($"Interview with id {id} not found");
        }
        await _interviewRepository.FinishInterviewAsync(id, request.Status, request.Transcript);
        return Ok($"Interview {id} finished with status {request.Status}");
    }

    [HttpDelete("interview/{id}")]
    public async Task<ActionResult<string>> DeleteInterview(int id)
    {
        Interview existing = await _interviewRepository.GetInterviewByIdAsync(id);
        if (existing == null)
        {
            return NotFound($"Interview with id {id} not found");
        }
        await _interviewRepository.DeleteInterviewAsync(id);
        return Ok($"Interview {id} deleted");
    }

    [HttpPatch("interview/{id}/submission")]
    public async Task<ActionResult<string>> UploadSubmission(int id, InterviewSubmissionRequest request)
    {
        Interview existing = await _interviewRepository.GetInterviewByIdAsync(id);
        if (existing == null)
        {
            return NotFound($"Interview with id {id} not found");
        }
        await _interviewRepository.UpdateStudentSubmissionAsync(id, request.StudentSubmission);
        return Ok($"Submission uploaded for interview {id}");
    }

    [HttpPost("interview/{id}/start")]
    public async Task<ActionResult<object>> StartInterview(int id)
    {
        Interview? interview = await _interviewRepository.GetInterviewByIdAsync(id);
        if (interview == null)
            return NotFound($"Interview {id} not found");

        var ecsSection = _config.GetSection("Ecs");
        var clusterArn = ecsSection["ClusterArn"];
        var taskDefinition = ecsSection["TaskDefinition"] ?? "interview-bot";
        var containerName = ecsSection["ContainerName"] ?? "interview-bot";
        var subnetIds = ecsSection.GetSection("SubnetIds").Get<List<string>>();
        var securityGroupIds = ecsSection.GetSection("SecurityGroupIds").Get<List<string>>();
        var assignPublicIp = ecsSection["AssignPublicIp"] == "DISABLED"
            ? AssignPublicIp.DISABLED
            : AssignPublicIp.ENABLED;

        if (string.IsNullOrEmpty(clusterArn) || subnetIds == null || securityGroupIds == null)
            return StatusCode(500, new { error = "ECS is not configured — fill in Ecs section of appsettings.json" });

        var request = new RunTaskRequest
        {
            Cluster = clusterArn,
            TaskDefinition = taskDefinition,
            LaunchType = LaunchType.FARGATE,
            NetworkConfiguration = new NetworkConfiguration
            {
                AwsvpcConfiguration = new AwsVpcConfiguration
                {
                    Subnets = subnetIds,
                    SecurityGroups = securityGroupIds,
                    AssignPublicIp = assignPublicIp,
                }
            },
            Overrides = new TaskOverride
            {
                ContainerOverrides =
                [
                    new ContainerOverride
                    {
                        Name = containerName,
                        Environment =
                        [
                            new Amazon.ECS.Model.KeyValuePair
                            {
                                Name = "INTERVIEW_ID",
                                Value = id.ToString()
                            }
                        ]
                    }
                ]
            }
        };

        var response = await _ecs.RunTaskAsync(request);

        if (response.Failures.Count > 0)
        {
            var failure = response.Failures[0];
            return StatusCode(502, new { error = $"ECS RunTask failed: {failure.Reason}" });
        }

        return Ok(new { status = "starting", interview_id = id });
    }

    [HttpGet("user/{id}")]
    public async Task<ActionResult<User>> GetUser(int id)
    {
        User user = await _interviewRepository.GetUserByIdAsync(id);
        if (user == null)
        {
            return NotFound("User not found");
        }
        return Ok(user);
    }

    [HttpPost("user")]
    public async Task<ActionResult<String>> AddUser(User user)
    {
        // Upsert: creates the user, or refreshes the display name/email for an
        // existing student (early records stored the student ID as the username).
        User u = await _interviewRepository.GetUserByIdAsync(user.StudentId);
        await _interviewRepository.AddUserAsync(user);
        return Ok(u == null ? "User added" : "User updated");
    }

    [HttpGet("zoom/{id}")]
    public async Task<ActionResult<Zoom>> GetZoom(int id)
    {
        Zoom zoom = await _interviewRepository.GetZoomByIdAsync(id);
        if (zoom == null)
        {
            return NotFound("Zoom not found");
        }
        return Ok(zoom);
    }

    [HttpPost("zoom")]
    public async Task<ActionResult<string>> AddZoom(Zoom zoom)
    {
        int id = await _interviewRepository.AddZoomAsync(zoom);
        return Ok($"Zoom added. Zoom Id: {id}");
    }

    [HttpGet("rubric/{id}")]
    public async Task<ActionResult<Rubric>> GetRubric(int id)
    {
        Rubric rubric = await _interviewRepository.GetRubricByIdAsync(id);
        if (rubric == null)
        {
            return NotFound("Rubric not found");
        }
        return  Ok(rubric);
    }

    [HttpPost("rubric")]
    public async Task<ActionResult<string>> AddRubric(Rubric rubric)
    {
        int id = await _interviewRepository.AddRubricAsync(rubric);
        return Ok($"Rubric added. Rubric Id: {id}");
    }

    [HttpGet("result/{id}")]
    public async Task<ActionResult<Result>> GetResult(int id)
    {
        Result result = await _interviewRepository.GetResultByIdAsync(id);
        if (result == null)
        {
            return NotFound("Result not found");
        }
        return Ok(result);
    }

    [HttpPost("result")]
    public async Task<ActionResult<int>> AddResult(Result result)
    {
        int id = await _interviewRepository.AddResultAsync(result);
        return Ok($"Result added. Result id: {id}");
    }

    // One result per interview, sharing the interview's id so the dashboard can
    // fetch it with the (already-known) interview id. Idempotent: re-marking
    // overwrites the existing result.
    [HttpPost("interview/{id}/result")]
    public async Task<ActionResult<int>> AddResultForInterview(int id, Result result)
    {
        Interview interview = await _interviewRepository.GetInterviewByIdAsync(id);
        if (interview == null)
        {
            return NotFound($"Interview with id {id} not found");
        }
        int resultId = await _interviewRepository.AddResultForInterviewAsync(id, result);
        return Ok($"Result added. Result id: {resultId}");
    }

    [HttpGet("assignment/{id}")]
    public async Task<ActionResult<Assignment>> GetAssignment(int id)
    {
        Assignment assignment = await _interviewRepository.GetAssignmentByIdAsync(id);
        if (assignment == null)
        {
            return NotFound("Assignment not found");
        }
        return Ok(assignment);
    }

    [HttpPost("assignment")]
    public async Task<ActionResult<int>> AddAssignment(Assignment assignment)
    {
        int id = await _interviewRepository.AddAssignmentAsync(assignment);
        return Ok($"Assignment added. Assignment id: {id}");
    }

    [HttpPut("assignment/{id}")]
    public async Task<ActionResult<string>> UpdateAssignment(int id, Assignment assignment)
    {
        Assignment existing = await _interviewRepository.GetAssignmentByIdAsync(id);
        if (existing == null)
        {
            return NotFound($"Assignment with id {id} not found");
        }
        await _interviewRepository.UpdateAssignmentAsync(id, assignment);
        return Ok($"Assignment updated. Assignment id: {id}");
    }

    // Reformat an uploaded plain-text rubric (any format) into the JSON string stored
    // in rubric.rubricContents. An LLM restructures it preserving content, with a
    // deterministic fallback so it never fails. Returns the JSON string (the frontend
    // persists it verbatim).
    [HttpPost("parse/rubric")]
    public async Task<ActionResult<string>> ParseRubric(TextParseRequest request)
    {
        try
        {
            return Ok(await _assessmentParser.ParseRubricAsync(request.Text ?? ""));
        }
        catch (ArgumentException ex)
        {
            return BadRequest(ex.Message);
        }
    }

    // Reformat an uploaded plain-text questions/areas-of-focus file into the JSON
    // string stored in assignment.questions.
    [HttpPost("parse/questions")]
    public async Task<ActionResult<string>> ParseQuestions(TextParseRequest request)
    {
        try
        {
            return Ok(await _assessmentParser.ParseQuestionsAsync(request.Text ?? ""));
        }
        catch (ArgumentException ex)
        {
            return BadRequest(ex.Message);
        }
    }

    [HttpPost("assignment/generate-assessment")]
    public async Task<ActionResult<GeneratedAssessment>> GenerateAssessment(GenerateAssessmentRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.KnowledgeBase))
            return BadRequest("knowledgeBase is required");
        if (request.NumQuestions < 1)
            return BadRequest("numQuestions must be at least 1");

        try
        {
            GeneratedAssessment result = await _assessmentGenerator.GenerateAsync(request);
            return Ok(result);
        }
        catch (Exception ex)
        {
            return StatusCode(502, new { error = $"Assessment generation failed: {ex.Message}" });
        }
    }

    [HttpDelete("assignment/{id}")]
    public async Task<ActionResult<string>> DeleteAssignment(int id)
    {
        Assignment existing = await _interviewRepository.GetAssignmentByIdAsync(id);
        if (existing == null)
        {
            return NotFound($"Assignment with id {id} not found");
        }
        // Cascades to the assignment's interviews (see repository) so no rows are
        // left referencing a deleted assignment.
        await _interviewRepository.DeleteAssignmentAsync(id);
        return Ok($"Assignment {id} deleted");
    }

    [HttpGet("instructor/{id}")]
    public async Task<ActionResult<Instructor>> GetInstructor(int id)
    {
        Instructor instructor = await _interviewRepository.GetInstructorByIdAsync(id);
        if (instructor == null)
        {
            return NotFound("Instructor not found");
        }
        return Ok(instructor);
    }

    [HttpPost("instructor")]
    public async Task<ActionResult<string>> AddInstructor(Instructor instructor)
    {
        Instructor existing = await _interviewRepository.GetInstructorByIdAsync(instructor.Id);
        if (existing != null)
        {
            return BadRequest("Instructor already exists");
        }
        await _interviewRepository.AddInstructorAsync(instructor);
        return Ok("Instructor added");
    }

    [HttpGet("class/{id}")]
    public async Task<ActionResult<Class>> GetClass(int id)
    {
        Class c = await _interviewRepository.GetClassByIdAsync(id);
        if (c == null)
        {
            return NotFound("Class not found");
        }
        return Ok(c);
    }

    [HttpPost("class")]
    public async Task<ActionResult<string>> AddClass(Class c)
    {
        Instructor instructor = await _interviewRepository.GetInstructorByIdAsync(c.InstructorId);
        if (instructor == null)
        {
            return NotFound($"Instructor with id {c.InstructorId} not found");
        }
        int id = await _interviewRepository.AddClassAsync(c);
        return Ok($"Class added. Class id: {id}");
    }

    [HttpPost("class/{id}/students")]
    public async Task<ActionResult<string>> AddStudentsToClass(int id, AddStudentsRequest request)
    {
        Class c = await _interviewRepository.GetClassByIdAsync(id);
        if (c == null)
        {
            return NotFound($"Class with id {id} not found");
        }

        var added = new List<int>();
        var skipped = new List<int>();
        foreach (int studentId in request.StudentIds)
        {
            User student = await _interviewRepository.GetUserByIdAsync(studentId);
            if (student == null)
            {
                skipped.Add(studentId);
                continue;
            }
            await _interviewRepository.AddStudentToClassAsync(id, studentId);
            added.Add(studentId);
        }
        return Ok(new { classId = id, added, skipped });
    }

    [HttpGet("class/{id}/students")]
    public async Task<ActionResult<IEnumerable<User>>> GetStudentsByClass(int id)
    {
        Class c = await _interviewRepository.GetClassByIdAsync(id);
        if (c == null)
        {
            return NotFound($"Class with id {id} not found");
        }
        IEnumerable<User> students = await _interviewRepository.GetStudentsByClassIdAsync(id);
        return Ok(students);
    }

    [HttpGet("instructor/{id}/assignments")]
    public async Task<ActionResult<IEnumerable<Assignment>>> GetAssignmentsByInstructor(int id)
    {
        Instructor instructor = await _interviewRepository.GetInstructorByIdAsync(id);
        if (instructor == null)
        {
            return NotFound($"Instructor with id {id} not found");
        }
        IEnumerable<Assignment> assignments = await _interviewRepository.GetAssignmentsByInstructorIdAsync(id);
        return Ok(assignments);
    }

    [HttpGet("instructor/{id}/interviews")]
    public async Task<ActionResult<IEnumerable<InterviewWithUser>>> GetInterviewsByInstructor(int id)
    {
        Instructor instructor = await _interviewRepository.GetInstructorByIdAsync(id);
        if (instructor == null)
        {
            return NotFound($"Instructor with id {id} not found");
        }
        IEnumerable<InterviewWithUser> interviews = await _interviewRepository.GetInterviewsByInstructorIdAsync(id);
        return Ok(interviews);
    }

    [HttpGet("instructor/{id}/classes")]
    public async Task<ActionResult<IEnumerable<Class>>> GetClassesByInstructor(int id)
    {
        Instructor instructor = await _interviewRepository.GetInstructorByIdAsync(id);
        if (instructor == null)
        {
            return NotFound($"Instructor with id {id} not found");
        }
        IEnumerable<Class> classes = await _interviewRepository.GetClassesByInstructorIdAsync(id);
        return Ok(classes);
    }

    [HttpGet("class/{id}/assignments")]
    public async Task<ActionResult<IEnumerable<Assignment>>> GetAssignmentsByClass(int id)
    {
        Class c = await _interviewRepository.GetClassByIdAsync(id);
        if (c == null)
        {
            return NotFound($"Class with id {id} not found");
        }
        IEnumerable<Assignment> assignments = await _interviewRepository.GetAssignmentsByClassIdAsync(id);
        return Ok(assignments);
    }
}
