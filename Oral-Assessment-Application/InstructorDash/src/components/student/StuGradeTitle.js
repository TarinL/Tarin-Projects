function StuGradeTitle({ studentName, assignmentName, interviewDate, grade, letter })
 {
  return (
    <div className="GradeTitle">

      <div>
        <h1 className="Gtitle">
          Oral Assessment Results
        </h1>

        <div className="Subtitles">
          <p>
            <span>Student:</span> {studentName}
          </p>

          <p>
            <span>Assignment:</span> {assignmentName}
          </p>

          <p>
            <span>Interview Date:</span> {interviewDate}
          </p>
        </div>
      </div>

      <div className="RightSection">

            <p className="SuggestedText">
                Grade
            </p>
              <h1 className="LetterGrade">{letter}</h1>
              <p className="NumericGrade">{grade}/100</p>
            </div>
    </div>
  );
}

export default StuGradeTitle;