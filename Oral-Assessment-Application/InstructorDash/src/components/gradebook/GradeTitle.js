function GradeTitle({
   studentName,
  assignmentName,
  interviewDate,

  grade,
  letter,
  isEditing,

  setLetter,
  setGrade,
  setIsEditing,
  readOnly = false
})

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
                Suggested Grade
            </p>

            {!isEditing ? (
              <>
                <h1 className="LetterGrade">{letter}</h1>
                <p className="NumericGrade">{grade}/100</p>
                {!readOnly && (
                  <button className="EditButton" onClick={() => setIsEditing(true)}>
                    Edit Grade
                  </button>
                )}
              </>
            ) : (
                <>
                <input
                    className="LetterInput"
                    value={letter}
                    onChange={(e) =>
                    setLetter(e.target.value)
                    }
                />

                <input
                    className="GradeInput"
                    type="number"
                    value={grade}
                    onChange={(e) =>
                    setGrade(e.target.value)
                    }
                />

                <button
                    className="SaveButton"
                    onClick={() => setIsEditing(false)}
                >
                    Save
                </button>
                </>
            )}

            </div>
    </div>
  );
}

export default GradeTitle;