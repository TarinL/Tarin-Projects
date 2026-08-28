import "../../styles/InstructorDash.css";

function EmptyInt() {
    return (
        <div className = "InitialBox">
            <label>Schedule Interviews</label>
            <div className = "text">
            <img src = "/calendar.svg" width = "30" height = "30" />
            <p>Select an assignment to schedule interviews</p>
            </div>
        </div>
    )
}

export default EmptyInt;