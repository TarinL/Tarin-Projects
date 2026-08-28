import "../../styles/InstructorDash.css";
import Card from "./Card";

function Tallys({assignments, interviews}) {
  console.log("interviews in tally:", interviews);
  const totalAssignments = assignments.length;
  const totalInterviews = interviews.length;
  const scheduled = interviews.filter(
    (interview) => interview.status?.toLowerCase() === "scheduled"
  ).length;
  const completed = interviews.filter(
    (interview) => interview.status?.toLowerCase() === "completed"
  ).length;

  return (
    <div className="Tallys">
      <Card text="Total Assignments" img="/Assignmentimg.svg" count={totalAssignments} />
      <Card text="Total Interviews" img="/calendar.svg" count={totalInterviews}/>
      <Card text="Scheduled" img="/clock.svg" count={scheduled}/>
      <Card text="Completed" img="/Tick.svg" count={completed}/>
    </div>
  );
}

export default Tallys;