using Dapper;
using InterviewApi.Models;

namespace InterviewApi.Data;
public class InterviewRepository : IInterviewRepository
{
    private readonly DbConnectionFactory _db;

    public InterviewRepository(DbConnectionFactory db)
    {
        _db = db;
    }
    
    public async Task<Interview?> GetInterviewByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QuerySingleOrDefaultAsync<Interview>(
            "SELECT * FROM interview WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddInterviewAsync(Interview interview)
    {
        using var connection = _db.Create();
        var id = await connection.ExecuteScalarAsync<int>(@"
            INSERT INTO interview (student_id, zoom_id, start_time, status, duration, due_date, additional_info, assignment_id, student_submission)
            VALUES (@StudentId, @ZoomId, @StartTime, @Status, @Duration, @DueDate, @AdditionalInfo, @AssignmentId, @StudentSubmission);
            SELECT LAST_INSERT_ID()", interview);
        return id;
    }

    public async Task UpdateInterviewAsync(int id, Interview interview)
    {
        using var connection = _db.Create();
        interview.Id = id;
        await connection.ExecuteAsync(@"
            UPDATE  interview SET
                student_id = @StudentId,
                zoom_id = @ZoomId,
                transcript = @Transcript,
                start_time = @StartTime,
                status = @Status,
                duration = @Duration,
                due_date = @DueDate,
                additional_info = @AdditionalInfo,
                assignment_id = @AssignmentId,
                student_submission = @StudentSubmission,
                result_id = @ResultId
            WHERE id = @Id", interview
        );
    }

    public async Task FinishInterviewAsync(int id, string status, string? transcript)
    {
        using var connection = _db.Create();
        // Stamp start_time with the actual completion time. Until now it held the
        // scheduled start (== due_date), so the gradebook's "Interview Date" showed
        // the due date instead of when the interview actually took place.
        await connection.ExecuteAsync(
            "UPDATE interview SET status = @Status, transcript = @Transcript, start_time = UTC_TIMESTAMP() WHERE id = @Id",
            new { Id = id, Status = status, Transcript = transcript }
        );
    }

    public async Task UpdateStudentSubmissionAsync(int id, string submission)
    {
        using var connection = _db.Create();
        await connection.ExecuteAsync(
            "UPDATE interview SET student_submission = @Submission WHERE id = @Id",
            new { Id = id, Submission = submission }
        );
    }

    public async Task DeleteInterviewAsync(int id)
    {
        using var connection = _db.Create();
        await connection.ExecuteAsync(
            "DELETE FROM interview WHERE id = @Id",
            new { Id = id }
        );
    }

    public async Task DeleteAssignmentAsync(int id)
    {
        // interview.assignment_id has a FK to assignment.id, so the assignment's
        // interviews must go first or the delete is rejected. This also keeps the
        // dashboard consistent (no interviews orphaned from a deleted assignment).
        using var connection = _db.Create();
        await connection.ExecuteAsync(@"
            DELETE FROM interview WHERE assignment_id = @Id;
            DELETE FROM assignment WHERE id = @Id;",
            new { Id = id }
        );
    }

   public async Task<IEnumerable<InterviewWithUser>> GetInterviewByStudentIdAsync(int id)
    {
        using var connection = _db.Create();
        var rows = await connection.QueryAsync<InterviewWithUser>(
            "SELECT * FROM interview WHERE student_id = @StudentId",
            new { StudentId = id }
        );
        // Every row belongs to the same student, so fetch the user once.
        var interviews = rows.ToList();
        if (interviews.Count > 0)
        {
            User? user = await GetUserByIdAsync(id);
            foreach (InterviewWithUser interview in interviews)
            {
                interview.User = user;
            }
        }
        return interviews;
    }

    public async Task<User?> GetUserByIdAsync(int studentId)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<User>(
            "SELECT * FROM user WHERE student_id = @Id",
            new { Id = studentId });
        return row;
    }

    public async Task<int> AddUserAsync(User user)
    {
        // Upsert so a returning student's display name/email is corrected on login
        // (early records stored the student ID as the username). The PK is
        // student_id, so a duplicate updates the existing row rather than failing.
        using var connection = _db.Create();
        await connection.ExecuteAsync(@"
            INSERT INTO user (student_id, username, email)
            VALUES (@StudentId, @Username, @Email)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                email = VALUES(email)", user);
        return user.StudentId;
    }

    public async Task<Rubric?> GetRubricByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Rubric>(
            "SELECT * FROM rubric WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddRubricAsync(Rubric rubric)
    {
        using var connection = _db.Create();
        int id = await connection.ExecuteScalarAsync<int>(@"
            INSERT INTO rubric (rubric_contents)
            VALUES (@RubricContents);
            SELECT LAST_INSERT_ID()", rubric);
        return id;
    }

    public async Task<Zoom?> GetZoomByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Zoom>(
            "SELECT * FROM zoom WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddZoomAsync(Zoom zoom)
    {
        using var connection = _db.Create();
        int id = await connection.ExecuteScalarAsync<int>(@"
            INSERT INTO zoom (url, meeting_id)
            VALUES (@Url, @MeetingId);
            SELECT LAST_INSERT_ID()", zoom);
        return id;
    }

    public async Task<Result?> GetResultByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Result>(
            "SELECT * FROM result WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddResultAsync(Result result)
    {
        using var connection = _db.Create();
        int id = await connection.ExecuteScalarAsync<int>(@"
        INSERT INTO result (transcript, grade, feedback)
        VALUES (@Transcript, @Grade, @Feedback);
        SELECT LAST_INSERT_ID()", result);
    return id;
    }

    public async Task<int> AddResultForInterviewAsync(int interviewId, Result result)
    {
        // One result per interview, sharing the interview's id. Idempotent so a
        // re-mark overwrites the existing row rather than failing on the PK.
        using var connection = _db.Create();
        result.Id = interviewId;
        await connection.ExecuteAsync(@"
            INSERT INTO result (id, transcript, grade, feedback)
            VALUES (@Id, @Transcript, @Grade, @Feedback)
            ON DUPLICATE KEY UPDATE
                transcript = VALUES(transcript),
                grade = VALUES(grade),
                feedback = VALUES(feedback);
            UPDATE interview SET result_id = @Id WHERE id = @Id;", result);
        return interviewId;
    }

    public async Task<int> AddAssignmentAsync(Assignment assignment)
    {
        using var connection = _db.Create();
        int id = await connection.ExecuteScalarAsync<int>(@"
        INSERT INTO assignment (name, contents, mode, knowledge_base, questions, class_id, rubric_id)
        VALUES (@Name, @Contents, @Mode, @KnowledgeBase, @Questions, @ClassId, @RubricId);
        SELECT LAST_INSERT_ID()", assignment);
        return id;
    }

    public async Task UpdateAssignmentAsync(int id, Assignment assignment)
    {
        using var connection = _db.Create();
        assignment.Id = id;
        await connection.ExecuteAsync(@"
            UPDATE assignment SET
                name = @Name,
                contents = @Contents,
                mode = @Mode,
                knowledge_base = @KnowledgeBase,
                questions = @Questions,
                class_id = @ClassId,
                rubric_id = @RubricId
            WHERE id = @Id", assignment
        );
    }

    public async Task<Assignment?> GetAssignmentByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Assignment>(
            "SELECT * FROM assignment WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<Instructor?> GetInstructorByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Instructor>(
            "SELECT * FROM instructor WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddInstructorAsync(Instructor instructor)
    {
        using var connection = _db.Create();
        await connection.ExecuteAsync(@"
            INSERT INTO instructor (id, name)
            VALUES (@Id, @Name)", instructor);
        return instructor.Id;
    }

    public async Task<Class?> GetClassByIdAsync(int id)
    {
        using var connection = _db.Create();
        var row = await connection.QueryFirstOrDefaultAsync<Class>(
            "SELECT * FROM `class` WHERE id = @Id",
            new { Id = id });
        return row;
    }

    public async Task<int> AddClassAsync(Class c)
    {
        using var connection = _db.Create();
        int id = await connection.ExecuteScalarAsync<int>(@"
            INSERT INTO `class` (name, instructor_id)
            VALUES (@Name, @InstructorId);
            SELECT LAST_INSERT_ID()", c);
        return id;
    }

    public async Task AddStudentToClassAsync(int classId, int studentId)
    {
        using var connection = _db.Create();
        await connection.ExecuteAsync(
            "INSERT IGNORE INTO class_student (class_id, student_id) VALUES (@ClassId, @StudentId)",
            new { ClassId = classId, StudentId = studentId });
    }

    public async Task<IEnumerable<User>> GetStudentsByClassIdAsync(int classId)
    {
        using var connection = _db.Create();
        var rows = await connection.QueryAsync<User>(@"
            SELECT u.* FROM user u
            JOIN class_student cs ON cs.student_id = u.student_id
            WHERE cs.class_id = @ClassId",
            new { ClassId = classId });
        return rows;
    }

    public async Task<IEnumerable<Assignment>> GetAssignmentsByClassIdAsync(int classId)
    {
        using var connection = _db.Create();
        var rows = await connection.QueryAsync<Assignment>(
            "SELECT * FROM assignment WHERE class_id = @ClassId",
            new { ClassId = classId });
        return rows;
    }

    public async Task<IEnumerable<Assignment>> GetAssignmentsByInstructorIdAsync(int instructorId)
    {
        using var connection = _db.Create();
        var rows = await connection.QueryAsync<Assignment>(@"
            SELECT a.* FROM assignment a
            JOIN `class` c ON a.class_id = c.id
            WHERE c.instructor_id = @InstructorId",
            new { InstructorId = instructorId });
        return rows;
    }

    public async Task<IEnumerable<InterviewWithUser>> GetInterviewsByInstructorIdAsync(int instructorId)
    {
        using var connection = _db.Create();
        var rows = await connection.QueryAsync<InterviewWithUser>(@"
            SELECT i.* FROM interview i
            JOIN assignment a ON i.assignment_id = a.id
            JOIN `class` c ON a.class_id = c.id
            WHERE c.instructor_id = @InstructorId",
            new { InstructorId = instructorId });

        // Rows span multiple students; fetch each distinct user once and map back.
        var interviews = rows.ToList();
        var users = new Dictionary<int, User?>();
        foreach (InterviewWithUser interview in interviews)
        {
            if (!users.TryGetValue(interview.StudentId, out User? user))
            {
                user = await GetUserByIdAsync(interview.StudentId);
                users[interview.StudentId] = user;
            }
            interview.User = user;
        }
        return interviews;
    }

    public async Task<IEnumerable<Class>> GetClassesByInstructorIdAsync(int instructorId)
    {
        using var connection = _db.Create();
        return await connection.QueryAsync<Class>(
            "SELECT * FROM `class` WHERE instructor_id = @InstructorId",
            new { InstructorId = instructorId });
    }
}